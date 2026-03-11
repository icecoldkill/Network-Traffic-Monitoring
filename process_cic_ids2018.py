# process_cic_ids2018.py
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import requests
import zipfile
import io
import random
import time

def download_sample_dataset(output_dir="./CSE-CIC-IDS2018/"):
    """
    Download a small sample of the CIC-IDS2018 dataset
    """
    print("Downloading a sample of the CIC-IDS2018 dataset...")
    os.makedirs(output_dir, exist_ok=True)
    
    # URL for one of the smaller files from the dataset
    # This is a sample URL - it might need to be updated
    url = "https://www.unb.ca/cic/datasets/ids-2018.html"
    
    print(f"Please visit {url} to download the dataset manually.")
    print("The dataset is quite large, so consider downloading just one file for testing.")
    print("After downloading, place the CSV files in the ./CSE-CIC-IDS2018/ directory.")
    
    # Option for synthetic data if download is not possible
    create_synthetic = input("Would you like to create synthetic data instead? (y/n): ")
    if create_synthetic.lower() == 'y':
        return create_synthetic_dataset(output_dir)
    return False

def create_synthetic_dataset(output_dir):
    """
    Create a synthetic dataset that mimics the structure of CIC-IDS2018
    """
    print("Creating synthetic network traffic dataset...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create random IPs
    def random_ip():
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
    
    # Generate timestamps
    current_time = time.time()
    timestamps = [current_time + i for i in range(20000)]
    
    # Create synthetic data
    data = {
        'Timestamp': [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) for ts in timestamps],
        'Source IP': [random_ip() for _ in range(20000)],
        'Destination IP': [random_ip() for _ in range(20000)],
        'Protocol': [random.choice(['TCP', 'UDP', 'ICMP']) for _ in range(20000)],
        'Source Port': [random.randint(1, 65535) for _ in range(20000)],
        'Destination Port': [random.randint(1, 65535) for _ in range(20000)],
        'Flow Duration': [random.randint(1, 10000) for _ in range(20000)],
        'Total Fwd Packets': [random.randint(1, 100) for _ in range(20000)],
        'Total Backward Packets': [random.randint(1, 100) for _ in range(20000)],
        'Total Length of Fwd Packets': [random.randint(40, 1500) for _ in range(20000)],
        'Total Length of Bwd Packets': [random.randint(40, 1500) for _ in range(20000)],
        'Label': ['BENIGN' if random.random() > 0.2 else random.choice(['DoS', 'PortScan', 'DDoS', 'BruteForce']) 
                 for _ in range(20000)]
    }
    
    df = pd.DataFrame(data)
    
    # Save synthetic dataset
    synthetic_file = os.path.join(output_dir, "synthetic_cic_ids2018.csv")
    df.to_csv(synthetic_file, index=False)
    print(f"Synthetic dataset created at {synthetic_file}")
    
    return True

def process_cic_ids2018(dataset_path, output_file, sample_size=None):
    """
    Process the CSE-CIC-IDS2018 dataset and prepare it for the network traffic visualizer.
    
    Args:
        dataset_path: Path to the dataset directory
        output_file: Path to save the processed dataset
        sample_size: Number of samples to take from each file (None for all)
    """
    # List of features to keep
    features = [
        'Timestamp', 'Source IP', 'Destination IP', 'Protocol', 
        'Source Port', 'Destination Port', 'Flow Duration', 'Total Fwd Packets',
        'Total Backward Packets', 'Total Length of Fwd Packets', 
        'Total Length of Bwd Packets', 'Label'
    ]
    
    # Simplified mapping for our needs
    # Map original features to our expected format
    feature_map = {
        'Source IP': 'src_ip',
        'Destination IP': 'dst_ip',
        'Protocol': 'protocol',
        'Total Length of Fwd Packets': 'packet_size',
        'Label': 'label'
    }
    
    all_data = []
    
    # Get all CSV files
    csv_files = []
    for root, _, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    
    print(f"Found {len(csv_files)} CSV files")
    
    # If no CSV files found, try to download or create a sample
    if len(csv_files) == 0:
        created = download_sample_dataset(dataset_path)
        if created:
            # Recheck for CSV files after download/creation
            csv_files = []
            for root, _, files in os.walk(dataset_path):
                for file in files:
                    if file.endswith(".csv"):
                        csv_files.append(os.path.join(root, file))
            print(f"Found {len(csv_files)} CSV files after dataset creation")
        
        if len(csv_files) == 0:
            raise ValueError("No CSV files found and couldn't create dataset. Please download the dataset manually.")
    
    # Process each file
    for file in csv_files:
        print(f"Processing {file}...")
        try:
            # First check if the file exists and is not empty
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                print(f"  - Skipping empty or non-existent file: {file}")
                continue
                
            # Read the first few rows to get column names
            df_sample = pd.read_csv(file, nrows=5)
            
            # Identify which columns from our features list exist in this file
            available_columns = [col for col in features if col in df_sample.columns]
            
            if not available_columns:
                print(f"  - Skipping file with no matching columns: {file}")
                continue
                
            # Read only needed columns to save memory
            df = pd.read_csv(file, usecols=available_columns)
            
            # Sample if requested
            if sample_size and len(df) > sample_size:
                df = df.sample(sample_size, random_state=42)
            
            # Check if Label column exists
            if 'Label' in df.columns:
                attack_count = df[df['Label'] != 'BENIGN'].shape[0]
                print(f"  - Attacks: {attack_count}, Benign: {df.shape[0] - attack_count}")
            
            all_data.append(df)
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    if not all_data:
        raise ValueError("No valid data found in any of the CSV files")
        
    # Combine all data
    print("Combining all data...")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Map features to our expected format
    processed_df = pd.DataFrame()
    for orig_col, new_col in feature_map.items():
        if orig_col in combined_df.columns:
            processed_df[new_col] = combined_df[orig_col]
    
    # Handle protocol conversion (if needed)
    if 'protocol' in processed_df.columns:
        # Convert protocol names to numbers if they're text
        if processed_df['protocol'].dtype == 'object':
            protocol_map = {'TCP': 6, 'UDP': 17, 'ICMP': 1}
            processed_df['protocol'] = processed_df['protocol'].map(protocol_map)
    
    # Create binary labels (0 for normal, 1 for attack)
    if 'label' in processed_df.columns:
        processed_df['is_anomaly'] = (processed_df['label'] != 'BENIGN').astype(int)
    
    # Save processed data
    processed_df.to_csv(output_file, index=False)
    print(f"Processed data saved to {output_file}")
    print(f"Total samples: {len(processed_df)}, Attacks: {processed_df['is_anomaly'].sum() if 'is_anomaly' in processed_df.columns else 'N/A'}")
    
    return processed_df

if __name__ == "__main__":
    # Example usage
    dataset_path = "./CSE-CIC-IDS2018/"  # Change to your dataset path
    output_file = "./data/processed_cic_ids2018.csv"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # Process with a sample size for each file (to make it manageable)
        df = process_cic_ids2018(dataset_path, output_file, sample_size=10000)
        
        # Split into train/test sets
        train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['is_anomaly'] if 'is_anomaly' in df.columns else None, random_state=42)
        
        # Save train/test sets
        train_df.to_csv("./data/cic_ids2018_train.csv", index=False)
        test_df.to_csv("./data/cic_ids2018_test.csv", index=False)
        
        print(f"Train set: {len(train_df)} samples")
        print(f"Test set: {len(test_df)} samples")
    except Exception as e:
        print(f"Error: {e}")
        print("\nAlternative: You can run the project with synthetic data using:")
        print("python main.py --mode collect --synthetic --samples 10000 --anomaly-ratio 0.2")