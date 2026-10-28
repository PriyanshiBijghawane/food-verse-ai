"""Verify the Render runtime imports and uses CPU-only PyTorch."""

import bcrypt
import cv2
import jwt
import numpy
import torch
import torchvision
import transformers

import main


if torch.version.cuda is not None:
    raise RuntimeError(
        f"Expected CPU-only PyTorch, found CUDA build {torch.version.cuda!r}."
    )

print(
    "Render runtime imports passed: "
    f"torch={torch.__version__}, torchvision={torchvision.__version__}, "
    f"transformers={transformers.__version__}, numpy={numpy.__version__}, "
    f"bcrypt={bcrypt.__version__}, PyJWT={jwt.__version__}, cv2={cv2.__version__}"
)
