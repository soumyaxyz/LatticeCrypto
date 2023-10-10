import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
df = pd.read_csv('Time_5000.csv', header=None)
df.columns = ['Signature Time (s)', 'Verification Time (s)']

# Convert seconds to milliseconds
df['Signature Time (ms)'] = df['Signature Time (s)'] * 1000
df['Verification Time (ms)'] = df['Verification Time (s)'] * 1000

# Sort the columns and round to the nearest millisecond
df = df.apply(lambda x: x.sort_values().round().astype(int))

# Function to plot histogram with parameterized bin size
def plot_histogram(data, bin_size, title):
    plt.hist(data, bins=range(min(data), max(data) + bin_size, bin_size), alpha=0.5)
    plt.xlabel('Time (ms)')
    plt.ylabel('Frequency')
    plt.title(title)

# Set the bin size (e.g., 1 ms)
bin_size = 1

# Create separate plots for signature and verification times
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plot_histogram(df['Signature Time (ms)'], bin_size, 'Signature Time Distribution (in ms)')

plt.subplot(1, 2, 2)
plot_histogram(df['Verification Time (ms)'], bin_size, 'Verification Time Distribution (in ms)')

plt.tight_layout()

# Show the plots
plt.show()
