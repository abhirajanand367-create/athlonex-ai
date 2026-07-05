from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pose.detector import PoseDetector

router = APIRouter()
pose_detector = PoseDetector()


@router.post("/detect")
async def detect_pose(file: UploadFile = File(...)):
    content = await file.read()
    landmarks = pose_detector.analyze_frame(content)
    if landmarks is None:
        raise HTTPException(status_code=400, detail="No pose detected")
    return {"landmarks": landmarks.model_dump()}


@router.post("/angles")
async def compute_angles(file: UploadFile = File(...)):
    content = await file.read()
    landmarks = pose_detector.analyze_frame(content)
    if landmarks is None:
        raise HTTPException(status_code=400, detail="No pose detected")

    angles = pose_detector._compute_key_angles(landmarks)
    return {"angles": angles}
