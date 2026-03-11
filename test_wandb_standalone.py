import wandb
import math
import random
import time
from dotenv import load_dotenv

# Load WANDB_API_KEY from .env
load_dotenv()

print("🚀 Starting Weights & Biases Standalone Test...")

# Initialize W&B run
run = wandb.init(
    project="network-anomaly-detection",
    name="baseline-test-run",
    config={
        "learning_rate": 0.01,
        "epochs": 10,
        "architecture": "Simulated Neural Network",
        "dataset": "Synthetic Network Flows"
    }
)

print(f"✅ Successfully initialized W&B Run: {run.url}")

# Simulate a training loop for 10 epochs
epochs = 10
print("\nSimulating Training Epochs...")
for epoch in range(1, epochs + 1):
    # Simulate decreasing loss and increasing accuracy
    simulated_loss = 2.0 * math.exp(-0.3 * epoch) + (random.random() * 0.1)
    simulated_acc = 1.0 - math.exp(-0.4 * epoch) - (random.random() * 0.05)
    
    print(f"Epoch {epoch}/{epochs} - loss: {simulated_loss:.4f} - accuracy: {simulated_acc:.4f}")
    
    # Log metrics to W&B
    wandb.log({
        "epoch": epoch,
        "loss": simulated_loss,
        "accuracy": simulated_acc
    })
    
    time.sleep(0.5)

print("\n🎉 Training Simulation Complete!")
wandb.finish()
print(f"View your live charts here: {run.url}")
