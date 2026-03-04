# Training AI Models with TensorFlow Using Tractus-X SDK

!!! warning "Experimental - Not Standardized"
    **This AI/ML integration approach is NOT part of the official Catena-X standard.**
    
    - This tutorial demonstrates a **custom implementation** for training TensorFlow models using dataspace data
    - There is currently **no standardized framework** for AI/ML integration in Catena-X
    - Data schemas, model formats, and sharing mechanisms shown here are **examples only**
    - **Do not use in production** without establishing proper governance and agreements with dataspace participants
    - Consult with your legal and compliance teams before implementing AI/ML workflows using dataspace data
    
    For standardized Catena-X use cases, refer to the official [Catena-X Standards](https://catena-x.net/en/standard-library).

## Overview

This tutorial demonstrates how to integrate the Tractus-X SDK with TensorFlow to train AI models using data retrieved from the Catena-X dataspace. You'll learn how to:

- Fetch training data from dataspace connectors
- Process and prepare data for machine learning
- Train TensorFlow models with dataspace data
- Publish results back to the dataspace

## Prerequisites

- Tractus-X SDK installed ([Installation Guide](getting-started.md))
- TensorFlow 2.x installed
- Access to a Catena-X dataspace connector
- Basic understanding of machine learning concepts

## Installation

Install the required dependencies:

```bash
pip install tractusx-sdk tensorflow numpy pandas scikit-learn
```

For GPU support (optional but recommended):

```bash
pip install tensorflow[and-cuda]
```

## Architecture Overview

The integration workflow consists of:

1. **Data Acquisition**: Use SDK consumer service to fetch data from dataspace
2. **Data Preprocessing**: Transform dataspace data into TensorFlow-compatible format
3. **Model Training**: Train TensorFlow models on the prepared dataset
4. **Result Publishing**: Optionally share trained models or predictions via dataspace

## Step 1: Configure Connector Services

First, set up the consumer service to access dataspace resources:

```python
import os
from tractusx_sdk.dataspace.services.connector import ServiceFactory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consumer connector configuration
consumer_connector = ServiceFactory.get_connector_consumer_service(
    dataspace_version="saturn",  # or "jupiter"
    base_url=os.getenv("CONSUMER_EDC_URL", "https://consumer-edc.example.com"),
    dma_path="/management",
    headers={
        "X-Api-Key": os.getenv("CONSUMER_API_KEY"),
        "Content-Type": "application/json"
    },
    logger=logger,
    verbose=True
)
```

## Step 2: Fetch Training Data from Dataspace

Retrieve datasets from dataspace providers:

```python
import json
import pandas as pd
from typing import List, Dict

def fetch_training_data(
    consumer_connector,
    provider_bpnl: str,
    provider_dsp_url: str,
    asset_id: str,
    policies: List[Dict] = None
) -> pd.DataFrame:
    """
    Fetch training data from a dataspace asset.
    
    Args:
        consumer_connector: Consumer connector service instance
        provider_bpnl: Business Partner Number of the data provider
        provider_dsp_url: DSP endpoint URL of provider's connector
        asset_id: ID of the asset containing training data
        policies: Optional list of usage policies
        
    Returns:
        pandas DataFrame with training data
    """
    try:
        # Fetch data using the consumer service
        response = consumer_connector.do_get_by_asset_id(
            counter_party_id=provider_bpnl,
            counter_party_address=provider_dsp_url,
            asset_id=asset_id,
            policies=policies,
            path="/data",  # Adjust path based on your asset structure
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} records from dataspace")
            return pd.DataFrame(data)
        else:
            raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
        raise

# Example usage
training_data = fetch_training_data(
    consumer_connector=consumer_connector,
    provider_bpnl="BPNL00000003AYRE",
    provider_dsp_url="https://provider-edc.example.com/api/v1/dsp",
    asset_id="urn:uuid:training-dataset-001",
    policies=None  # Accept any policy (testing only)
)

print(f"Dataset shape: {training_data.shape}")
print(training_data.head())
```

## Step 3: Preprocess Data for TensorFlow

Transform the dataspace data into a format suitable for TensorFlow:

```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import tensorflow as tf

def preprocess_data(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str,
    test_size: float = 0.2
) -> tuple:
    """
    Preprocess dataspace data for TensorFlow training.
    
    Args:
        df: DataFrame with raw data
        feature_columns: List of column names to use as features
        target_column: Name of the target/label column
        test_size: Fraction of data to use for testing
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test, scaler, encoder)
    """
    # Handle missing values
    df = df.dropna(subset=feature_columns + [target_column])
    
    # Extract features and target
    X = df[feature_columns].values
    y = df[target_column].values
    
    # Encode categorical target if necessary
    encoder = None
    if y.dtype == 'object' or y.dtype.name == 'category':
        encoder = LabelEncoder()
        y = encoder.fit_transform(y)
    
    # Split into train/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Convert to TensorFlow tensors
    X_train = tf.constant(X_train, dtype=tf.float32)
    X_test = tf.constant(X_test, dtype=tf.float32)
    y_train = tf.constant(y_train, dtype=tf.int32)
    y_test = tf.constant(y_test, dtype=tf.int32)
    
    logger.info(f"Preprocessed data - Train: {X_train.shape}, Test: {X_test.shape}")
    
    return X_train, X_test, y_train, y_test, scaler, encoder

# Example preprocessing
feature_cols = ["temperature", "pressure", "vibration", "speed"]
target_col = "failure_type"

X_train, X_test, y_train, y_test, scaler, encoder = preprocess_data(
    df=training_data,
    feature_columns=feature_cols,
    target_column=target_col,
    test_size=0.2
)
```

## Step 4: Build and Train TensorFlow Model

Create and train a neural network model:

```python
from tensorflow import keras
from tensorflow.keras import layers, callbacks

def build_model(
    input_dim: int,
    num_classes: int,
    hidden_layers: List[int] = [128, 64, 32]
) -> keras.Model:
    """
    Build a TensorFlow neural network model.
    
    Args:
        input_dim: Number of input features
        num_classes: Number of output classes
        hidden_layers: List of hidden layer sizes
        
    Returns:
        Compiled Keras model
    """
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.BatchNormalization()
    ])
    
    # Add hidden layers with dropout
    for units in hidden_layers:
        model.add(layers.Dense(units, activation='relu'))
        model.add(layers.Dropout(0.3))
    
    # Output layer
    if num_classes == 2:
        model.add(layers.Dense(1, activation='sigmoid'))
        loss = 'binary_crossentropy'
        metrics = ['accuracy', keras.metrics.AUC()]
    else:
        model.add(layers.Dense(num_classes, activation='softmax'))
        loss = 'sparse_categorical_crossentropy'
        metrics = ['accuracy']
    
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss=loss,
        metrics=metrics
    )
    
    return model

# Build the model
num_features = X_train.shape[1]
num_classes = len(np.unique(y_train))

model = build_model(
    input_dim=num_features,
    num_classes=num_classes,
    hidden_layers=[128, 64, 32]
)

# Display model architecture
model.summary()

# Configure callbacks
early_stopping = callbacks.EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)

reduce_lr = callbacks.ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=5,
    min_lr=1e-7
)

# Train the model
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_test, y_test),
    epochs=100,
    batch_size=32,
    callbacks=[early_stopping, reduce_lr],
    verbose=1
)

# Evaluate the model
test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
logger.info(f"Model trained - Test Accuracy: {test_accuracy:.4f}")
```

## Step 5: Advanced - Federated Learning Setup

!!! warning \"Additional Governance Required for Federated Learning\"\n    Federated learning across multiple dataspace participants introduces **additional complexity and risks**:\n    \n    - Requires **multi-party agreements** on model architecture, training protocols, and data contributions\n    - Participants may still be able to **infer information** about other participants' data\n    - No standardized Catena-X framework exists for federated learning workflows\n    - **Regulatory compliance** becomes more complex with cross-border data usage\n    - Requires robust **coordination mechanisms** and trust frameworks\n    \n    Consult with legal experts and establish formal governance agreements before implementing federated learning in production.\n\nFor privacy-preserving distributed training across multiple dataspace participants:

```python
import tensorflow_federated as tff

def create_federated_data(
    consumer_connector,
    provider_configs: List[Dict]
) -> List[tf.data.Dataset]:
    """
    Fetch data from multiple providers for federated learning.
    
    Args:
        consumer_connector: Consumer connector service
        provider_configs: List of dicts with provider info
        
    Returns:
        List of TensorFlow datasets (one per provider)
    """
    federated_datasets = []
    
    for config in provider_configs:
        # Fetch data from each provider
        provider_data = fetch_training_data(
            consumer_connector=consumer_connector,
            provider_bpnl=config["bpnl"],
            provider_dsp_url=config["dsp_url"],
            asset_id=config["asset_id"],
            policies=config.get("policies")
        )
        
        # Preprocess locally
        X, _, y, _, _, _ = preprocess_data(
            df=provider_data,
            feature_columns=config["features"],
            target_column=config["target"],
            test_size=0.0  # Use all data for training
        )
        
        # Create TensorFlow dataset
        dataset = tf.data.Dataset.from_tensor_slices((X, y))
        dataset = dataset.shuffle(1000).batch(32)
        federated_datasets.append(dataset)
    
    logger.info(f"Created {len(federated_datasets)} federated datasets")
    return federated_datasets

# Example federated learning configuration
# Note: Requires tensorflow-federated package
# pip install tensorflow-federated
```

## Step 6: Publish Results to Dataspace

!!! danger "Attention! - Publishing ML Results"
    **Publishing AI/ML model results to the dataspace requires extreme caution!**
    
    **Legal and Compliance Risks:**
    
    - ML predictions may contain **inferred personal data** or sensitive business information
    - Publishing results could violate **GDPR, data sovereignty agreements**, or contractual obligations
    - You may be liable for **incorrect predictions** that cause financial or operational harm
    - Original data usage policies may **explicitly prohibit** using data for ML training or sharing results
    
    **Technical Risks:**
    
    - Model outputs could **reveal training data** (model inversion attacks)
    - Predictions may perpetuate or amplify **biases** from training data
    - No standardized vocabulary exists for ML prediction assets in Catena-X
    
    **Before Publishing:**
    
    1. Obtain **explicit permission** from all data providers whose data was used for training
    2. Conduct a **legal review** of data usage agreements and applicable regulations
    3. Perform **bias and fairness audits** on your model
    4. Implement **differential privacy** or other privacy-preserving techniques
    5. Establish clear **liability and disclaimer** statements
    6. Use **standardized Catena-X governance frameworks** when available
    
    **The code below is for educational purposes only. Do not use in production without proper legal and technical safeguards.**

Share trained model predictions or insights back to the dataspace:

```python
def publish_predictions(
    provider_connector,
    model: keras.Model,
    scaler: StandardScaler,
    input_data: pd.DataFrame,
    asset_id: str
) -> dict:
    """
    Generate predictions and publish them as an asset in the dataspace.
    
    Args:
        provider_connector: Provider connector service
        model: Trained TensorFlow model
        scaler: Fitted StandardScaler
        input_data: New data to make predictions on
        asset_id: ID for the predictions asset
        
    Returns:
        Created asset information
    """
    # Generate predictions
    X_new = scaler.transform(input_data.values)
    predictions = model.predict(X_new)
    
    # Prepare results
    results = {
        "predictions": predictions.tolist(),
        "confidence_scores": predictions.max(axis=1).tolist(),
        "model_version": "1.0.0",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Create asset in dataspace
    # Note: You'll need a provider connector service configured
    asset = provider_connector.create_asset(
        asset_id=asset_id,
        base_url="https://your-backend.example.com/predictions",
        dct_type="https://example.com/taxonomy#MLPredictions",
        version="1.0",
        description="ML predictions from TensorFlow model"
    )
    
    logger.info(f"Published predictions as asset: {asset_id}")
    return asset
```

## Complete Example: End-to-End Pipeline

Here's a complete example combining all steps:

```python
#!/usr/bin/env python3
"""
Complete example: Train TensorFlow model on Catena-X dataspace data
"""

import os
import logging
import pandas as pd
import tensorflow as tf
from tractusx_sdk.dataspace.services.connector import ServiceFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # 1. Initialize connector
    logger.info("Step 1: Initializing dataspace connector...")
    consumer = ServiceFactory.get_connector_consumer_service(
        dataspace_version="saturn",
        base_url=os.getenv("CONSUMER_EDC_URL"),
        dma_path="/management",
        headers={
            "X-Api-Key": os.getenv("CONSUMER_API_KEY"),
            "Content-Type": "application/json"
        }
    )
    
    # 2. Fetch training data
    logger.info("Step 2: Fetching training data from dataspace...")
    training_data = fetch_training_data(
        consumer_connector=consumer,
        provider_bpnl="BPNL00000003AYRE",
        provider_dsp_url="https://provider-edc.example.com/api/v1/dsp",
        asset_id="urn:uuid:training-dataset-001"
    )
    
    # 3. Preprocess data
    logger.info("Step 3: Preprocessing data...")
    X_train, X_test, y_train, y_test, scaler, encoder = preprocess_data(
        df=training_data,
        feature_columns=["feature1", "feature2", "feature3", "feature4"],
        target_column="label"
    )
    
    # 4. Build and train model
    logger.info("Step 4: Building and training TensorFlow model...")
    model = build_model(
        input_dim=X_train.shape[1],
        num_classes=len(tf.unique(y_train)[0])
    )
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=50,
        batch_size=32,
        verbose=2
    )
    
    # 5. Evaluate model
    logger.info("Step 5: Evaluating model...")
    test_loss, test_accuracy = model.evaluate(X_test, y_test)
    logger.info(f"Final Test Accuracy: {test_accuracy:.4f}")
    
    # 6. Save model
    logger.info("Step 6: Saving model...")
    model.save("dataspace_trained_model.keras")
    logger.info("Model saved successfully")
    
    return model, history

if __name__ == "__main__":
    model, history = main()
```

## Best Practices

!!! warning \"Remember: Non-Standard Implementation\"\n    These best practices apply to the **experimental AI/ML integration** shown in this tutorial, which is **not part of official Catena-X standards**. Always prioritize compliance with:\n    \n    - Official Catena-X governance frameworks\n    - Your organization's legal and compliance requirements\n    - Data provider agreements and usage policies\n    - Industry-specific regulations (e.g., automotive, healthcare)\n\n### Data Privacy and Security

- **Usage Policies**: Always specify appropriate usage policies when fetching data
- **Data Anonymization**: Anonymize sensitive data before training
- **Model Privacy**: Use differential privacy techniques for sensitive datasets
- **Access Control**: Implement proper authentication and authorization

### Performance Optimization

- **Batch Processing**: Use batched requests for large datasets
- **Caching**: Cache preprocessed data to avoid redundant fetches
- **GPU Acceleration**: Utilize GPU for faster training when available
- **Distributed Training**: Use federated learning for multi-party scenarios

### Model Management

- **Versioning**: Track model versions and training data sources
- **Monitoring**: Monitor model performance over time
- **Retraining**: Set up automated retraining pipelines
- **Documentation**: Document data sources, preprocessing steps, and model architecture

## Troubleshooting

### Common Issues

**Issue**: `ConnectionError` when fetching data
```python
# Solution: Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_with_retry(consumer_connector, **kwargs):
    return fetch_training_data(consumer_connector, **kwargs)
```

**Issue**: Memory errors with large datasets
```python
# Solution: Use data generators
def create_data_generator(consumer_connector, batch_size=1000):
    # Implement pagination or streaming
    offset = 0
    while True:
        batch = fetch_training_data(
            consumer_connector,
            path=f"/data?offset={offset}&limit={batch_size}"
        )
        if batch.empty:
            break
        yield batch
        offset += batch_size
```

**Issue**: Incompatible data formats
```python
# Solution: Add robust data validation
from pydantic import BaseModel, ValidationError

class TrainingDataSchema(BaseModel):
    feature1: float
    feature2: float
    label: int

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    validated_records = []
    for _, row in df.iterrows():
        try:
            validated_records.append(TrainingDataSchema(**row.to_dict()).dict())
        except ValidationError as e:
            logger.warning(f"Skipping invalid record: {e}")
    return pd.DataFrame(validated_records)
```

## Next Steps

- Explore [Notification API](notification-api.md) for model update notifications
- Learn about [Industry Core Hub Use Case](../how-to-guides/ic-hub-use-case/industry-core-hub-overview.md)
- Review [Authentication & Security](../core-concepts/authentication-security/authentication.md) best practices
- Implement federated learning with TensorFlow Federated

## Additional Resources

- [TensorFlow Documentation](https://www.tensorflow.org/guide)
- [Catena-X Standards](https://catena-x.net/association/standardization/)
- [Tractus-X SDK API Reference](../api-reference/dataspace-library/index.md)
- [Privacy-Preserving ML](https://www.tensorflow.org/responsible_ai/privacy)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)