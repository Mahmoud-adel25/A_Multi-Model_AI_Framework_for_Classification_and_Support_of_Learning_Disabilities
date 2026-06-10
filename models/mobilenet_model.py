"""
MobileNet V3 Large Classifier for Handwriting Classification
Matches training notebook: only classifier[3] is replaced
"""

import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights


class MobileNetClassifier(nn.Module):
    """
    MobileNet V3 Large for handwriting classification.
    Only classifier[3] is modified (the final Linear layer).
    
    Original classifier structure:
      (0): Linear(960, 1280)
      (1): Hardswish()
      (2): Dropout(p=0.2)
      (3): Linear(1280, 1000) <- only this is replaced
    """
    
    def __init__(self, num_classes: int = 2, pretrained_backbone: bool = False):
        super(MobileNetClassifier, self).__init__()
        
        if pretrained_backbone:
            self.model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.DEFAULT)
        else:
            self.model = mobilenet_v3_large(weights=None)
        
        # Only replace classifier[3] - matches training notebook
        in_features = self.model.classifier[3].in_features  # 1280
        self.model.classifier[3] = nn.Linear(in_features, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)
    
    def load_state_dict(self, state_dict, strict=True):
        """Load state dict into the inner model."""
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
