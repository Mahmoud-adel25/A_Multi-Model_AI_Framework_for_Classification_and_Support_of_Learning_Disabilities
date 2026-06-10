"""
Custom CNN Model for Handwriting Classification
Matches the training notebook: 28x28 grayscale input, 3 pooling layers -> 3x3 feature maps
CNN checkpoint is 3-class (fc3 [3, 256]); inference maps to binary in model_loader.

Architecture verified against Final code.ipynb:
- fc1: Linear(2304, 512), fc2: Linear(512, 256), fc3: Linear(256, num_classes)
- Forward: conv blocks -> view -> dropout(relu(fc1)) -> dropout(relu(fc2)) -> fc3
- Dropout is disabled at inference via model.eval().
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CNNClassifier(nn.Module):
    """
    Custom CNN architecture for handwriting classification
    Input: 28x28 grayscale images
    Output: 3 classes in checkpoint (Normal / Reversal / Dyslexia Indicator); app maps to binary.
    """
    def __init__(self, num_classes=3):
        super(CNNClassifier, self).__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        
        # Pooling and dropout
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.5)
        
        # Fully connected layers
        # After 3 pooling operations: 28 -> 14 -> 7 -> 3
        self.fc1 = nn.Linear(256 * 3 * 3, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, num_classes)
        
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # Conv block 1: 28x28 -> 14x14
        x = self.pool(self.relu(self.bn1(self.conv1(x))))
        
        # Conv block 2: 14x14 -> 7x7
        x = self.pool(self.relu(self.bn2(self.conv2(x))))
        
        # Conv block 3: 7x7 -> 3x3
        x = self.pool(self.relu(self.bn3(self.conv3(x))))
        
        # Conv block 4: 3x3 -> 3x3 (no pooling)
        x = self.relu(self.bn4(self.conv4(x)))
        
        # Flatten and FC layers
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        
        return x


# Alias for backward compatibility
CustomCNN = CNNClassifier
