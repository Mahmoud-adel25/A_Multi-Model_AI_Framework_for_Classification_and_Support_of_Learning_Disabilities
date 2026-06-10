"""
EfficientNet-B0 Classifier for Handwriting Classification
Matches training notebook: only classifier[1] is replaced
"""

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


class EfficientNetClassifier(nn.Module):
    """
    EfficientNet-B0 for handwriting classification.
    Only the final classifier layer is modified (classifier[1]).
    """
    
    def __init__(self, num_classes: int = 2, pretrained_backbone: bool = False):
        super(EfficientNetClassifier, self).__init__()
        
        if pretrained_backbone:
            self.model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        else:
            self.model = efficientnet_b0(weights=None)
        
        # Only replace classifier[1] - matches training notebook
        in_features = self.model.classifier[1].in_features  # 1280
        self.model.classifier[1] = nn.Linear(in_features, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)
    
    def load_state_dict(self, state_dict, strict=True):
        """Load state dict into the inner model."""
        # Try loading directly into inner model first
        try:
            return self.model.load_state_dict(state_dict, strict=strict)
        except RuntimeError:
            # If keys don't match, try with 'model.' prefix stripped
            new_sd = {}
            for k, v in state_dict.items():
                if k.startswith("model."):
                    new_sd[k[6:]] = v
                else:
                    new_sd[k] = v
            return self.model.load_state_dict(new_sd, strict=strict)
    
    def state_dict(self):
        return self.model.state_dict()
