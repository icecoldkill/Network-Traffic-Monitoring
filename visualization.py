# visualization.py
# Add at the top of visualization.py
import threading
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend for thread-safety
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# rest of your imports...
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cv2
from matplotlib.colors import LinearSegmentedColormap
import os
from datetime import datetime
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib
import networkx as nx
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Switch to non-interactive backend if we're in a thread
if threading.current_thread() is not threading.main_thread():
    # Save the current backend
    current_backend = matplotlib.get_backend()
    # Use Agg for non-interactive plotting
    matplotlib.use('Agg')
    # Note: make sure to restore the backend when done if needed

class NetworkTrafficVisualizer:
    def __init__(self, output_dir="./visualizations"):
        import matplotlib.pyplot as plt
        import seaborn as sns
        import cv2
        import numpy as np
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import networkx as nx
        from datetime import datetime

        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Set style - use default style if seaborn is not available
        try:
            sns.set_style("whitegrid")
            plt.style.use('seaborn-v0_8')  # Use the correct style name for newer matplotlib
        except Exception as e:
            logger.warning(f"Could not set seaborn style: {str(e)}. Using default style.")
            plt.style.use('default')

        # Custom colormap for better visualization
        self.traffic_cmap = LinearSegmentedColormap.from_list('traffic_cmap', 
                                                             ['darkblue', 'blue', 'green', 
                                                              'yellow', 'orange', 'red'])
        
        # Set figure parameters
        matplotlib.rcParams['figure.figsize'] = [12, 6]
        matplotlib.rcParams['figure.dpi'] = 100
    
    def _preprocess_data(self, df):
        """Preprocess the data for visualization"""
        # Convert timestamp to datetime if it's not already
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Convert protocols to numeric if they're not
        if 'protocol' in df.columns and df['protocol'].dtype == 'object':
            protocol_map = {'TCP': 1, 'UDP': 2, 'ICMP': 3}
            df['protocol_num'] = df['protocol'].map(lambda x: protocol_map.get(x, 0))
        
        return df
        
    def create_time_series(self, df, time_col='timestamp', value_col='packet_size', 
                          title='Network Traffic Over Time'):
        """Create an interactive time series plot using Plotly"""
        try:
            df = self._preprocess_data(df)
            
            # Ensure we have the required columns
            if time_col not in df.columns or value_col not in df.columns:
                raise ValueError(f"Required columns '{time_col}' and/or '{value_col}' not found in data")
            
            # Create the figure
            fig = px.line(df, x=time_col, y=value_col, 
                         title=title,
                         labels={value_col: 'Packet Size (bytes)', 
                                time_col: 'Time'})
            
            # Update layout for better appearance
            fig.update_layout(
                plot_bgcolor='white',
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
                hovermode='x unified',
                height=500
            )
            
            # Add range slider and buttons
            fig.update_xaxes(
                rangeslider_visible=True,
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def create_heatmap(self, df, x_col='source_ip', y_col='destination_port', 
                      z_col='packet_size', title='Network Traffic Heatmap'):
        """Create an interactive heatmap of network traffic"""
        try:
            df = self._preprocess_data(df)
            
            # Ensure we have the required columns
            required_cols = [x_col, y_col, z_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Required columns not found in data: {', '.join(missing_cols)}")
            
            # Create pivot table for heatmap
            pivot_df = df.pivot_table(
                index=y_col, 
                columns=x_col, 
                values=z_col, 
                aggfunc='sum',
                fill_value=0
            )
            
            # Create the heatmap
            fig = px.imshow(
                pivot_df.values,
                labels=dict(x="Source IP", y="Destination Port", color=z_col),
                x=pivot_df.columns,
                y=pivot_df.index,
                aspect="auto",
                title=title,
                color_continuous_scale='Viridis'
            )
            
            # Update layout for better appearance
            fig.update_layout(
                xaxis_title="Source IP",
                yaxis_title="Destination Port",
                coloraxis_colorbar=dict(title=z_col),
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def create_protocol_distribution(self, df, protocol_col='protocol', 
                                   title='Protocol Distribution'):
        """Create a pie chart of protocol distribution"""
        try:
            df = self._preprocess_data(df)
            
            if protocol_col not in df.columns:
                raise ValueError(f"Protocol column '{protocol_col}' not found in data")
            
            # Count protocol occurrences
            protocol_counts = df[protocol_col].value_counts().reset_index()
            protocol_counts.columns = ['protocol', 'count']
            
            # Create the pie chart
            fig = px.pie(
                protocol_counts,
                values='count',
                names='protocol',
                title=title,
                hole=0.3,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            
            # Update layout for better appearance
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
            )
            
            fig.update_layout(
                uniformtext_minsize=12,
                uniformtext_mode='hide',
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating protocol distribution: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def create_temporal_heatmap(self, df, feature='packet_size', time_bins=24, ip_bins=32):
        """Create a temporal heatmap of network traffic data by time and IP"""
        try:
            df = self._preprocess_data(df)
            
            # Generate time bins
            df['time_bin'] = pd.cut(pd.to_datetime(df['timestamp']).dt.hour, bins=time_bins)
            
            # Generate IP bins (using last octet of source IP)
            if 'src_ip' in df.columns:
                df['ip_bin'] = df['src_ip'].apply(lambda x: int(x.split('.')[-1]) % ip_bins)
            
            # Aggregate data by time_bin and ip_bin
            pivot_data = df.pivot_table(index='time_bin', columns='ip_bin', 
                                      values=feature, aggfunc='mean', fill_value=0)
            
            # Create the heatmap
            fig = px.imshow(
                pivot_data.values,
                labels=dict(x="IP Bin", y="Time Bin", color=feature),
                x=pivot_data.columns,
                y=pivot_data.index.astype(str),
                aspect="auto",
                title=f'Network Traffic Heatmap: {feature} by Time and Source IP',
                color_continuous_scale='Viridis'
            )
            
            # Update layout for better appearance
            fig.update_layout(
                xaxis_title='Source IP (last octet modulo {})'.format(ip_bins),
                yaxis_title='Hour of Day',
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating temporal heatmap: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def create_protocol_spectrogram(self, df, window_size=100, step=20):
        """Create a spectrogram-like visualization of protocol usage over time"""
        try:
            df = self._preprocess_data(df)
            
            # Ensure we have protocol_num
            if 'protocol_num' not in df.columns and 'protocol' in df.columns:
                protocol_map = {'TCP': 1, 'UDP': 2, 'ICMP': 3}
                df['protocol_num'] = df['protocol'].map(lambda x: protocol_map.get(x, 0))
            
            if 'protocol_num' not in df.columns:
                raise ValueError("No protocol information available in the data")
            
            # Create the spectrogram data
            protocols = sorted(df['protocol_num'].unique())
            n_windows = (len(df) - window_size) // step + 1
            
            if n_windows <= 0:
                raise ValueError("Not enough data for protocol spectrogram")
            
            spectrogram = np.zeros((len(protocols), n_windows))
            
            for i in range(n_windows):
                start_idx = i * step
                end_idx = start_idx + window_size
                
                window_data = df['protocol_num'].iloc[start_idx:end_idx]
                
                for j, protocol in enumerate(protocols):
                    spectrogram[j, i] = np.sum(window_data == protocol) / window_size
            
            # Create the figure
            protocol_labels = {1: 'TCP', 2: 'UDP', 3: 'ICMP'}
            y_ticktext = [protocol_labels.get(p, f'Protocol {p}') for p in protocols]
            
            fig = px.imshow(
                spectrogram,
                labels=dict(x="Time Window", y="Protocol", color="Proportion"),
                y=y_ticktext,
                aspect="auto",
                title='Protocol Usage Over Time',
                color_continuous_scale='Viridis'
            )
            
            # Update layout for better appearance
            fig.update_layout(
                xaxis_title="Time Window",
                yaxis_title="Protocol",
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating protocol spectrogram: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def visualize_traffic_flow(self, df, time_window=10):
        """Create a visualization of traffic flow between IPs"""
        try:
            df = self._preprocess_data(df)
            
            # Ensure we have the required columns
            required_cols = ['src_ip', 'dst_ip', 'timestamp']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Required columns not found in data: {', '.join(missing_cols)}")
            
            # Group data into time windows
            df['time_window'] = pd.to_datetime(df['timestamp']).dt.floor(f'{time_window}min')
            
            # Get the most recent time window
            latest_window = df['time_window'].max()
            window_data = df[df['time_window'] == latest_window]
            
            # Count traffic between source and destination IPs
            flow_counts = window_data.groupby(['src_ip', 'dst_ip']).size().reset_index(name='count')
            
            if len(flow_counts) == 0:
                raise ValueError("No traffic flow data available for the selected time window")
            
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add edges with weights
            for _, row in flow_counts.iterrows():
                G.add_edge(row['src_ip'], row['dst_ip'], weight=row['count'])
            
            # Create a Plotly figure
            fig = go.Figure()
            
            # Get positions for nodes using spring layout
            pos = nx.spring_layout(G)
            
            # Add edges
            edge_x = []
            edge_y = []
            edge_weights = []
            
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                
                # Add line for edge
                fig.add_trace(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    line=dict(width=G[edge[0]][edge[1]]['weight']*0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))
                
                # Add arrow
                fig.add_annotation(
                    x=x1,
                    y=y1,
                    ax=x0,
                    ay=y0,
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=G[edge[0]][edge[1]]['weight']*0.5,
                    arrowcolor='#888'
                )
            
            # Add nodes
            node_x = []
            node_y = []
            node_text = []
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(f"IP: {node}")
            
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=node_text,
                textposition="top center",
                hoverinfo='text',
                marker=dict(
                    color='lightblue',
                    size=20,
                    line=dict(color='black', width=1)
                )
            ))
            
            # Update layout
            fig.update_layout(
                title=f'Network Traffic Flow at {latest_window}',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=600
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating traffic flow visualization: {str(e)}")
            # Return an empty figure with error message
            fig = go.Figure()
            fig.update_layout(
                title=f"Error: {str(e)}",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                    {
                        "text": str(e),
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"}
                    }
                ]
            )
            return fig
    
    def create_visualization_dataset(self, df, n_samples=100, window_size=50, 
                                   image_size=(128, 128)):
        """Create a dataset of images for model training
        
        Args:
            df: Input DataFrame with network traffic data
            n_samples: Number of samples to generate
            window_size: Size of the time window for each sample
            image_size: Size of the output images (width, height)
            
        Returns:
            Tuple of (images, labels) where images is a numpy array of images
            and labels is a numpy array of corresponding labels
        """
        try:
            df = self._preprocess_data(df)
            
            # Initialize arrays to store images and labels
            images = np.zeros((n_samples, *image_size, 3), dtype=np.uint8)
            labels = np.zeros(n_samples, dtype=int)
            
            # Generate samples
            for i in range(n_samples):
                # Randomly select a time window
                if len(df) > window_size:
                    start_idx = np.random.randint(0, len(df) - window_size)
                    window_data = df.iloc[start_idx:start_idx + window_size]
                else:
                    window_data = df
                
                # Create a visualization for this window
                # Here we'll use the time series visualization as an example
                # You can modify this to use other visualization methods
                fig = self.create_time_series(
                    window_data, 
                    title=f'Sample {i+1}'
                )
                
                # Convert the figure to an image
                img_bytes = fig.to_image(format='png')
                img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                
                # Resize the image to the desired dimensions
                img = cv2.resize(img, image_size)
                
                # Store the image and a dummy label (you should replace this with actual labels)
                images[i] = img
                labels[i] = 0  # Replace with actual label logic
            
            return images, labels
            
        except Exception as e:
            logger.error(f"Error creating visualization dataset: {str(e)}")
            return None, None
            img1 = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            img1 = img1.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            img1 = cv2.resize(img1, image_size)
            plt.close()
            
            # 2. Protocol distribution
            protocol_counts = window_df['protocol'].value_counts()
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.bar(protocol_counts.index, protocol_counts.values, color='green')
            ax.set_xticks([])
            ax.set_yticks([])
            
            fig.canvas.draw()
            img2 = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            img2 = img2.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            img2 = cv2.resize(img2, image_size)
            plt.close()
            
            # Combine the visualizations (side by side)
            combined_img = np.concatenate((img1, img2), axis=1)
            
            images.append(combined_img)
            
            # Add label if available
            if has_labels:
                # If any packet in the window is an anomaly, label the window as anomaly
                labels.append(1 if window_df['anomaly'].any() else 0)
        
        # Convert to numpy arrays
        X = np.array(images)
        
        if has_labels:
            y = np.array(labels)
            return X, y
        else:
            return X, None