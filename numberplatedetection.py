from ultralytics import YOLO
import cv2
import easyocr
import numpy as np
import csv
import os
import serial
import time
from datetime import datetime
# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# Load YOLO model
model = YOLO("yolo11x.pt")
# Initialize EasyOCR
reader = easyocr.Reader(['en'])
# Registered vehicle numbers
registered_vehicles = {"MH12AB1234", "KA09CC9876", "DL5CAB4321", "21BH0001AA"}
# Output folders
os.makedirs("plates", exist_ok=True)
# CSV log file
csv_file = "access_log.csv"
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Plate_Number", "Access_Status"])
# ---------------------------------------------------------
# ARDUINO CONNECTION
# ---------------------------------------------------------
try:
    arduino = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)
    print("✅ Arduino connected!")
except Exception as e:
    print("❌ Arduino connection failed:", e)
    arduino = None
# ---------------------------------------------------------
# FUNCTION TO SEND DATA TO ARDUINO
# ---------------------------------------------------------
def send_to_arduino(msg):
    if arduino:
        try:
            command = (msg + "\r\n").encode()
            arduino.write(command)
            arduino.flush()
            print(f"[VS Code → Arduino] Sent: {msg}")
        except Exception as e:
            print(f"Failed to send: {e}")
# ---------------------------------------------------------
# CAMERA SETUP
# ---------------------------------------------------------
print("🔍 Connecting to camera...")
#cap = cv2.VideoCapture("http://192.168.113.131:4747/mjpegfeed") 
#cap = cv2.VideoCapture("http://192.168.113.131:4747/video")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not detected!")
    exit()
print("🚀 Smart Gate System Running. Press Q to exit.")
# ---------------------------------------------------------
# DETECTION LOOP
# ---------------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Cannot read frame.")
        break
    results = model.predict(frame, imgsz=640, conf=0.5, verbose=False)
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            plate_crop = frame[y1:y2, x1:x2]
            if plate_crop.size > 0:
                gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                ocr_result = reader.readtext(gray_plate)
                detected_text = ""
                for (bbox, text, prob) in ocr_result:
                    detected_text += text.upper().replace(" ", "").strip()
                if detected_text:
                    access_status = "GRANTED" if detected_text in registered_vehicles else "DENIED"
                    color = (0, 255, 0) if access_status == "GRANTED" else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{detected_text} - {access_status}",
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    filename = f"plates/{detected_text}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, plate_crop)
                    # Save entry log
                    with open(csv_file, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, detected_text, access_status])
                    print(f"[{timestamp}] Plate: {detected_text} → Access {access_status}")
                    # ---------------------------------------------------------
                    # SEND COMMAND TO ARDUINO
                    # ---------------------------------------------------------
                    if access_status == "GRANTED":
                        send_to_arduino("GRANT")
                    else:
                        send_to_arduino("DENY") 
    cv2.imshow("🚗 Smart Gate Entry System", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
print("🛑 Program exited successfully.")