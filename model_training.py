# model_training.py
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.applications import VGG16, ResNet50
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, roc_auc_score, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns
import time
import wandb
from wandb.keras import WandbCallback
try:
    import tensorflow as tf
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout
    HAS_TF = True
except ImportError:
    print("TensorFlow not available. Using alternative implementation.")
    HAS_TF = False
    
# Import scikit-learn (correctly named package)
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class NetworkAnomalyDetector:
    def __init__(self, model_dir="./models"):
        self.model_dir = model_dir
        self.model = None
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
            
class NetworkAnomalyDetector:
    def __init__(self, model_dir="./models"):
        self.model_dir = model_dir
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        self.model = None
    
    def build_simple_cnn(self, input_shape):
        """Build a simple CNN model for anomaly detection"""
        model = Sequential([
            Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
            MaxPooling2D((2, 2)),
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(optimizer='adam',
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
        
        return model
    
    def build_transfer_learning_model(self, input_shape, base_model='vgg16'):
        """Build a transfer learning model using pre-trained weights"""
        if base_model == 'vgg16':
            base = VGG16(weights='imagenet', include_top=False, input_shape=input_shape)
        elif base_model == 'resnet50':
            base = ResNet50(weights='imagenet', include_top=False, input_shape=input_shape)
        else:
            raise ValueError(f"Unsupported base model: {base_model}")
        
        # Freeze the base model layers
        for layer in base.layers:
            layer.trainable = False
        
        # Add custom layers for our task
        x = Flatten()(base.output)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(128, activation='relu')(x)
        output = Dense(1, activation='sigmoid')(x)
        
        model = Model(inputs=base.input, outputs=output)
        
        model.compile(optimizer='adam',
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
        
        return model
    
    def train_model(self, X_train, y_train, model_type='simple_cnn', batch_size=32, epochs=20, 
                   validation_split=0.2):
        """Train the anomaly detection model"""
        # Build the appropriate model
        input_shape = X_train.shape[1:]
        
        if model_type == 'simple_cnn':
            self.model = self.build_simple_cnn(input_shape)
        elif model_type == 'vgg16' or model_type == 'resnet50':
            self.model = self.build_transfer_learning_model(input_shape, model_type)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
            
        # Calculate model architecture size
        trainable_params = sum([tf.keras.backend.count_params(w) for w in self.model.trainable_weights])
        non_trainable_params = sum([tf.keras.backend.count_params(w) for w in self.model.non_trainable_weights])
            
        # Initialize Weights & Biases Run with advanced configurations
        wandb.init(
            project="network-anomaly-detection",
            config={
                "model_type": model_type,
                "batch_size": batch_size,
                "epochs": epochs,
                "validation_split": validation_split,
                "architecture": "CNN" if model_type == "simple_cnn" else "TransferLearning",
                "trainable_parameters": trainable_params,
                "non_trainable_parameters": non_trainable_params,
                "total_parameters": trainable_params + non_trainable_params
            }
        )
        
        # Data augmentation to improve model robustness
        datagen = ImageDataGenerator(
            rotation_range=10,
            width_shift_range=0.1,
            height_shift_range=0.1,
            zoom_range=0.1,
            horizontal_flip=False,
            fill_mode='nearest'
        )
        
        # Setup callbacks
        model_checkpoint = ModelCheckpoint(
            f"{self.model_dir}/{model_type}_best_model.h5",
            monitor='val_accuracy',
            save_best_only=True,
            mode='max',
            verbose=1
        )
        
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        )
        
        # Train the model
        history = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=batch_size),
            steps_per_epoch=len(X_train) // batch_size,
            epochs=epochs,
            validation_split=validation_split,
            callbacks=[model_checkpoint, early_stopping, WandbCallback(save_model=False)]
        )
        
        # Save the final model
        self.model.save(f"{self.model_dir}/{model_type}_final_model.h5")
        
        # Plot training history
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Training Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.title('Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f"{self.model_dir}/{model_type}_training_history.png")
        plt.close()
        
        # Log final training charts to W&B
        wandb.log({"training_history_chart": wandb.Image(f"{self.model_dir}/{model_type}_training_history.png")})
        
        return history
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate the model performance"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Make predictions
        y_pred_prob = self.model.predict(X_test)
        y_pred = (y_pred_prob > 0.5).astype(int).flatten()
        
        # Calculate metrics
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
        
        # Print classification report
        print(classification_report(y_test, y_pred))
        
        # Create confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.savefig(f"{self.model_dir}/confusion_matrix.png")
        plt.close()
        
        # Calculate evaluation metrics
        metrics = {
            'accuracy': np.mean(y_pred == y_test),
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
        # Enhance dictionary with advanced AUC if valid targets exist
        try:
            auc = roc_auc_score(y_test, y_pred_prob)
            metrics['roc_auc'] = auc
        except Exception:
            pass # Handle single class testing gracefully
            
        # Generate Precision-Recall Curve Visualization
        try:
            pr_precision, pr_recall, _ = precision_recall_curve(y_test, y_pred_prob)
            plt.figure(figsize=(8, 6))
            plt.plot(pr_recall, pr_precision, marker='.', label='CNN Model')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Precision-Recall Curve')
            plt.savefig(f"{self.model_dir}/pr_curve.png")
            plt.close()
            wandb.log({"precision_recall_curve": wandb.Image(f"{self.model_dir}/pr_curve.png")})
        except Exception:
            pass
        
        # Log final test metrics and confusion matrix to W&B
        wandb.log({
            "test_accuracy": metrics['accuracy'],
            "test_precision": metrics['precision'],
            "test_recall": metrics['recall'],
            "test_f1_score": metrics['f1_score'],
            "test_roc_auc": metrics.get('roc_auc', None),
            "confusion_matrix_chart": wandb.Image(f"{self.model_dir}/confusion_matrix.png")
        })
        wandb.finish()
        
        return metrics
    
    def load_model(self, model_path):
        """Load a trained model"""
        self.model = tf.keras.models.load_model(model_path)
        return self.model