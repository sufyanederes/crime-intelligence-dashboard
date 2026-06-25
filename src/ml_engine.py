"""
Machine Learning and Explainable AI (XAI) Module
Handles model training, prediction, and feature importance extraction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
from typing import Tuple, Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLEngine:
    """
    Machine Learning Engine with Explainable AI capabilities
    Uses Random Forest for optimal interpretability and performance balance
    """
    
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        """
        Initialize ML Engine
        
        Args:
            n_estimators (int): Number of trees in Random Forest
            random_state (int): Random seed for reproducibility
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced'
        )
        self.feature_names = None
        self.model_metrics = {}
        self.is_trained = False
        self.feature_importance_data = None
        
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, float]:
        """
        Train Random Forest model on crime data
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target labels
            test_size (float): Test set proportion
            
        Returns:
            Dict: Training metrics (accuracy, precision, recall, F1-score)
        """
        try:
            self.feature_names = X.columns.tolist()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
            
            # Train model
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # Evaluate
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)
            
            self.model_metrics = {
                'train_accuracy': accuracy_score(y_train, y_pred_train),
                'test_accuracy': accuracy_score(y_test, y_pred_test),
                'precision': precision_score(y_test, y_pred_test, average='weighted', zero_division=0),
                'recall': recall_score(y_test, y_pred_test, average='weighted', zero_division=0),
                'f1_score': f1_score(y_test, y_pred_test, average='weighted', zero_division=0),
                'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist()
            }
            
            logger.info(f"Model trained. Metrics: {self.model_metrics}")
            return self.model_metrics
            
        except Exception as e:
            logger.error(f"Training error: {str(e)}")
            raise
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            X (pd.DataFrame): Feature matrix
            
        Returns:
            np.ndarray: Predicted crime categories
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            predictions = self.model.predict(X)
            logger.info(f"Made predictions for {len(X)} samples")
            return predictions
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities (confidence scores)
        
        Args:
            X (pd.DataFrame): Feature matrix
            
        Returns:
            np.ndarray: Probability matrix for each class
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self, top_n: int = 5) -> Dict[str, float]:
        """
        Extract feature importance scores for explainability
        
        Args:
            top_n (int): Number of top features to return
            
        Returns:
            Dict: Feature names and their importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        feature_importance = {
            self.feature_names[i]: float(importances[i])
            for i in indices
        }
        
        self.feature_importance_data = feature_importance
        return feature_importance
    
    def explain_prediction(self, X_sample: pd.DataFrame, prediction: int) -> Dict[str, Any]:
        """
        Generate explainable AI output for a single prediction
        Shows which features most influenced the decision
        
        Args:
            X_sample (pd.DataFrame): Single sample for prediction
            prediction (int): Model's predicted class
            
        Returns:
            Dict: Explanation with feature contributions
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Get confidence
        proba = self.model.predict_proba(X_sample)[0]
        confidence = float(np.max(proba))
        
        # Get feature importance
        importances = self.model.feature_importances_
        
        # Create feature attribution
        feature_contributions = {
            self.feature_names[i]: {
                'value': float(X_sample[self.feature_names[i]].values[0]),
                'importance': float(importances[i])
            }
            for i in range(len(self.feature_names))
        }
        
        explanation = {
            'predicted_class': int(prediction),
            'confidence': confidence,
            'feature_contributions': feature_contributions,
            'top_contributing_features': dict(
                sorted(feature_contributions.items(), 
                       key=lambda x: x[1]['importance'], 
                       reverse=True)[:3]
            )
        }
        
        logger.info(f"Generated explanation for prediction {prediction}")
        return explanation
    
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to disk
        
        Args:
            filepath (str): Path to save model (.pkl file)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Cannot save untrained model.")
        
        try:
            joblib.dump(self.model, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, filepath: str) -> None:
        """
        Load trained model from disk
        
        Args:
            filepath (str): Path to load model (.pkl file)
        """
        try:
            self.model = joblib.load(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_metrics(self) -> Dict[str, float]:
        """
        Retrieve stored model metrics
        
        Returns:
            Dict: Model performance metrics
        """
        return self.model_metrics


if __name__ == "__main__":
    # Example usage
    # engine = MLEngine()
    # engine.train(X_train, y_train)
    # predictions = engine.predict(X_test)
    # importance = engine.get_feature_importance()
    # explanation = engine.explain_prediction(X_sample, prediction)
    pass
