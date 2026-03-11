import matplotlib
matplotlib.use('Agg')
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure tensorflow doesn't print too much info
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

from model_training import NetworkAnomalyDetector

print("🚀 Starting Weights & Biases Training Test...")

# 1. Generate Fake Network Flow "Images" (e.g., 64x64 matrices with 3 channels)
# 100 samples total
num_samples = 100
input_shape = (64, 64, 3)

print("Generating synthetic network packet data for training...")
X_train = np.random.rand(num_samples, *input_shape).astype('float32')

# Generate labels: 0 for normal, 1 for anomaly
y_train = np.random.randint(0, 2, num_samples)

# 2. Initialize the Detector 
detector = NetworkAnomalyDetector(model_dir="./models")

# 3. Trigger the Training Loop (W&B will automatically hook into this)
print("Initiating Keras Training Loop (W&B tracking enabled)...")
try:
    detector.train_model(
        X_train=X_train, 
        y_train=y_train, 
        model_type='simple_cnn', 
        batch_size=16, 
        epochs=3, 
        validation_split=0.2
    )

    print("\n✅ Training Complete!")
    
    # 4. Trigger evaluation to generate confusion matrix for W&B
    print("Evaluating model to generate Confusion Matrix...")
    X_test = np.random.rand(20, *input_shape).astype('float32')
    y_test = np.random.randint(0, 2, 20)
    
    metrics = detector.evaluate_model(X_test, y_test)
    print("\n✅ Metrics and Charts successfully logged to your W&B Dashboard!")
    print(f"Final Accuracy: {metrics['accuracy']:.2f}")

except Exception as e:
    print(f"\n❌ Error during training: {e}")
