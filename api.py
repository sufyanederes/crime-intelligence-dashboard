"""
FastAPI Backend Microservice
Handles concurrent ML inference, caching, and API endpoints
Enterprise-grade async architecture for scalability
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import asyncio
from functools import lru_cache

from src.ml_engine import MLEngine
from src.data_engine import DataEngine
from src.auth import RoleBasedAccessControl
from src.audit_logger import AuditLog, AuditEventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Crime Intelligence Dashboard API",
    description="ML-powered crime classification and analysis API",
    version="1.0.0"
)

# Initialize core components
ml_engine = MLEngine()
data_engine = DataEngine()
rbac = RoleBasedAccessControl()
audit_logger = AuditLog()

# In-memory cache for frequent queries (Redis would be production equivalent)
prediction_cache = {}
hotspot_cache = {}


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class CrimeFeatures(BaseModel):
    """Input features for crime classification"""
    hour: int
    day_of_week: int
    latitude: float
    longitude: float
    location_type: int


class PredictionRequest(BaseModel):
    """Request model for prediction"""
    user_id: str
    features: CrimeFeatures


class PredictionResponse(BaseModel):
    """Response model for prediction"""
    prediction_id: str
    predicted_class: int
    confidence: float
    explanation: Dict[str, Any]
    audit_entry_id: str


class HotspotRequest(BaseModel):
    """Request model for hotspot analysis"""
    user_id: str
    top_n: int = 10
    radius_km: float = 1.0


class HotspotResponse(BaseModel):
    """Response model for hotspot analysis"""
    hotspots: List[Dict[str, Any]]
    timestamp: str


class UserLoginRequest(BaseModel):
    """User login request"""
    user_id: str
    password_hash: str


class AuditReportRequest(BaseModel):
    """Request for audit report"""
    user_id: str
    start_date: str
    end_date: str


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_current_user(request: Request) -> Dict[str, str]:
    """
    Validate user from request headers
    In production, this would verify JWT tokens
    """
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user_id": user_id}


# ============================================================================
# Prediction Endpoints
# ============================================================================

@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict_crime(
    request: PredictionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Classify a crime based on input features
    Returns prediction with XAI explanation
    """
    try:
        user_id = request.user_id
        features = request.features
        
        # Check permissions
        if not rbac.check_permission(user_id, "classify_crime"):
            audit_logger.log_permission_denied(
                user_id,
                rbac.users.get(user_id).role if user_id in rbac.users else "unknown",
                "crime_classification",
                "User lacks permission"
            )
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Check cache first
        cache_key = f"{features.hour}_{features.day_of_week}_{features.latitude}_{features.longitude}"
        if cache_key in prediction_cache:
            cached = prediction_cache[cache_key]
            logger.info(f"Cache hit for prediction: {cache_key}")
            return cached
        
        # Prepare features
        import pandas as pd
        X = pd.DataFrame({
            'Hour': [features.hour],
            'DayOfWeek': [features.day_of_week],
            'Latitude': [features.latitude],
            'Longitude': [features.longitude],
            'LocationType_Encoded': [features.location_type]
        })
        
        # Make prediction
        prediction = ml_engine.predict(X)[0]
        proba = ml_engine.predict_proba(X)[0]
        confidence = float(max(proba))
        
        # Generate explanation
        explanation = ml_engine.explain_prediction(X, prediction)
        
        # Log prediction for audit trail
        feature_importance = ml_engine.get_feature_importance()
        audit_entry_id = audit_logger.log_prediction(
            user_id=user_id,
            user_role=rbac.users[user_id].role if user_id in rbac.users else "unknown",
            input_features={
                'hour': features.hour,
                'day_of_week': features.day_of_week,
                'latitude': features.latitude,
                'longitude': features.longitude,
                'location_type': features.location_type
            },
            predicted_class=int(prediction),
            confidence_score=confidence,
            feature_importance=feature_importance
        )
        
        # Create response
        response = PredictionResponse(
            prediction_id=f"pred_{int(datetime.now().timestamp())}",
            predicted_class=int(prediction),
            confidence=confidence,
            explanation=explanation,
            audit_entry_id=audit_entry_id
        )
        
        # Cache result
        prediction_cache[cache_key] = response
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        audit_logger.log_system_error(
            error_message=str(e),
            error_type="prediction_error",
            user_id=request.user_id,
            context={"features": request.features.dict()}
        )
        raise HTTPException(status_code=500, detail="Prediction failed")


# ============================================================================
# Hotspot Analysis Endpoints
# ============================================================================

@app.post("/api/v1/hotspots", response_model=HotspotResponse)
async def get_hotspots(
    request: HotspotRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Identify crime hotspots based on historical data
    Returns top N hotspot locations
    """
    try:
        user_id = request.user_id
        
        # Check permissions
        if not rbac.check_permission(user_id, "view_maps"):
            audit_logger.log_permission_denied(
                user_id,
                rbac.users.get(user_id).role if user_id in rbac.users else "unknown",
                "hotspot_analysis",
                "User lacks permission"
            )
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Check cache
        cache_key = f"hotspots_{request.top_n}_{request.radius_km}"
        if cache_key in hotspot_cache:
            logger.info(f"Cache hit for hotspots: {cache_key}")
            return hotspot_cache[cache_key]
        
        # Generate mock hotspots (in production, query from PostGIS database)
        hotspots = [
            {
                "latitude": 3.1357 + (i * 0.01),
                "longitude": 101.6880 + (i * 0.01),
                "incident_count": 150 - (i * 10),
                "crime_types": ["PropertyTheft", "AggravatedAssault"],
                "risk_level": "High" if i < 3 else "Medium"
            }
            for i in range(request.top_n)
        ]
        
        # Log data access
        audit_logger.log_data_access(
            user_id=user_id,
            user_role=rbac.users[user_id].role if user_id in rbac.users else "unknown",
            resource_accessed="hotspot_analysis",
            query_params={"top_n": request.top_n, "radius_km": request.radius_km}
        )
        
        response = HotspotResponse(
            hotspots=hotspots,
            timestamp=datetime.now().isoformat()
        )
        
        # Cache result
        hotspot_cache[cache_key] = response
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotspot analysis error: {str(e)}")
        audit_logger.log_system_error(
            error_message=str(e),
            error_type="hotspot_error",
            user_id=request.user_id
        )
        raise HTTPException(status_code=500, detail="Hotspot analysis failed")


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/v1/login")
async def login(request: UserLoginRequest):
    """
    Authenticate user and return session token
    """
    try:
        success, token = rbac.authenticate_user(request.user_id, request.password_hash)
        
        if not success:
            audit_logger.log_permission_denied(
                request.user_id,
                "unknown",
                "login",
                "Invalid credentials"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        audit_logger.log_user_event(
            user_id=request.user_id,
            user_role=rbac.users[request.user_id].role,
            event_type=AuditEventType.USER_LOGIN,
            details={"ip": "127.0.0.1"}
        )
        
        return {"token": token, "user_id": request.user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/api/v1/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout user and close session
    """
    try:
        user_id = current_user["user_id"]
        rbac.logout_user(user_id)
        
        audit_logger.log_user_event(
            user_id=user_id,
            user_role=rbac.users[user_id].role if user_id in rbac.users else "unknown",
            event_type=AuditEventType.USER_LOGOUT,
            details={}
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


# ============================================================================
# Audit and Compliance Endpoints
# ============================================================================

@app.post("/api/v1/audit-report")
async def get_audit_report(
    request: AuditReportRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate compliance audit report
    Only authorized users can access
    """
    try:
        user_id = request.user_id
        
        # Check permissions - only commanders and analysts
        if not rbac.check_permission(user_id, "view_audit_logs"):
            audit_logger.log_permission_denied(
                user_id,
                rbac.users.get(user_id).role if user_id in rbac.users else "unknown",
                "audit_report_access",
                "User lacks permission"
            )
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Parse dates
        from datetime import datetime as dt
        start_date = dt.fromisoformat(request.start_date)
        end_date = dt.fromisoformat(request.end_date)
        
        # Generate report
        report = audit_logger.generate_compliance_report(start_date, end_date)
        
        audit_logger.log_data_access(
            user_id=user_id,
            user_role=rbac.users[user_id].role,
            resource_accessed="audit_report",
            query_params={"start_date": request.start_date, "end_date": request.end_date}
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit report error: {str(e)}")
        raise HTTPException(status_code=500, detail="Report generation failed")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """
    System health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_trained": ml_engine.is_trained,
        "cache_size": {
            "predictions": len(prediction_cache),
            "hotspots": len(hotspot_cache)
        }
    }


@app.get("/api/v1/model-metrics")
async def get_model_metrics(current_user: Dict = Depends(get_current_user)):
    """
    Get model performance metrics
    """
    user_id = current_user["user_id"]
    
    if not rbac.check_permission(user_id, "view_dashboard"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return ml_engine.get_model_metrics()


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
