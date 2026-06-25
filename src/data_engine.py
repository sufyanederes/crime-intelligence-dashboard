"""
Data Ingestion and Cleaning Module
Handles raw crime data loading, validation, and feature engineering
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataEngine:
    """
    Automated data cleaning and feature extraction pipeline
    Processes raw crime data and prepares it for ML model consumption
    """
    
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
        self.feature_columns = ['Hour', 'DayOfWeek', 'Latitude', 'Longitude', 'LocationType_Encoded']
        self.target_column = 'CrimeCategory_Encoded'
        self.location_type_mapping = {
            'Commercial': 0,
            'Residential': 1,
            'PublicTransit': 2
        }
        self.crime_category_mapping = {
            'PropertyTheft': 0,
            'AggravatedAssault': 1,
            'CommercialBurglary': 2
        }
        
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load raw crime data from CSV file
        
        Args:
            filepath (str): Path to crime data CSV file
            
        Returns:
            pd.DataFrame: Loaded data
        """
        try:
            self.raw_data = pd.read_csv(filepath)
            logger.info(f"Loaded {len(self.raw_data)} records from {filepath}")
            return self.raw_data
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def validate_data(self) -> Dict[str, any]:
        """
        Validate data integrity and identify issues
        
        Returns:
            Dict: Validation report with missing values and data quality metrics
        """
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        validation_report = {
            'total_records': len(self.raw_data),
            'missing_values': self.raw_data.isnull().sum().to_dict(),
            'duplicate_records': self.raw_data.duplicated().sum(),
            'data_types': self.raw_data.dtypes.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Validation Report: {validation_report}")
        return validation_report
    
    def clean_data(self) -> pd.DataFrame:
        """
        Clean raw data by handling missing values and outliers
        
        Returns:
            pd.DataFrame: Cleaned dataset
        """
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        df = self.raw_data.copy()
        
        # Remove duplicates
        df = df.drop_duplicates()
        logger.info(f"Removed duplicates. Records: {len(df)}")
        
        # Handle missing values
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype in ['float64', 'int64']:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
        
        logger.info("Missing values handled")
        
        # Remove obvious outliers (coordinates outside valid ranges)
        df = df[(df['Latitude'].between(-90, 90)) & (df['Longitude'].between(-180, 180))]
        logger.info(f"Removed coordinate outliers. Records: {len(df)}")
        
        self.processed_data = df
        return df
    
    def extract_features(self) -> pd.DataFrame:
        """
        Extract and engineer features from raw data
        
        Returns:
            pd.DataFrame: Feature-engineered dataset
        """
        if self.processed_data is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")
        
        df = self.processed_data.copy()
        
        # Extract temporal features
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Hour'] = df['Timestamp'].dt.hour
            df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
        
        # Encode categorical features
        if 'LocationType' in df.columns:
            df['LocationType_Encoded'] = df['LocationType'].map(self.location_type_mapping)
        
        if 'CrimeCategory' in df.columns:
            df['CrimeCategory_Encoded'] = df['CrimeCategory'].map(self.crime_category_mapping)
        
        # Select only required features
        required_cols = self.feature_columns + [self.target_column]
        available_cols = [col for col in required_cols if col in df.columns]
        df_final = df[available_cols].dropna()
        
        logger.info(f"Features extracted. Final dataset shape: {df_final.shape}")
        return df_final
    
    def get_feature_statistics(self) -> Dict:
        """
        Get statistical summary of features
        
        Returns:
            Dict: Feature statistics (mean, std, min, max, etc.)
        """
        if self.processed_data is None:
            raise ValueError("Data not processed. Call clean_data() first.")
        
        stats = {
            'count': len(self.processed_data),
            'numeric_summary': self.processed_data.describe().to_dict(),
            'categorical_unique': {col: self.processed_data[col].nunique() 
                                   for col in self.processed_data.select_dtypes(include=['object']).columns}
        }
        return stats
    
    def anonymize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove PII and anonymize sensitive fields
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Anonymized dataframe
        """
        df_anon = df.copy()
        
        # Remove PII columns if present
        pii_columns = ['Name', 'Phone', 'Email', 'Address', 'VictimID', 'OfficerID']
        df_anon = df_anon.drop(columns=[col for col in pii_columns if col in df_anon.columns])
        
        # Aggregate coordinates to block centroids (reduce precision)
        if 'Latitude' in df_anon.columns and 'Longitude' in df_anon.columns:
            df_anon['Latitude'] = (df_anon['Latitude'] * 100).round() / 100
            df_anon['Longitude'] = (df_anon['Longitude'] * 100).round() / 100
        
        logger.info("Data anonymized: PII removed and coordinates aggregated")
        return df_anon


if __name__ == "__main__":
    # Example usage
    engine = DataEngine()
    # df = engine.load_data("data/crime_data.csv")
    # validation = engine.validate_data()
    # cleaned = engine.clean_data()
    # features = engine.extract_features()
    # print(engine.get_feature_statistics())
