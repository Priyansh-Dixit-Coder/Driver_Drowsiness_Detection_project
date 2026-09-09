import cv2
import time
import winsound
from twilio.rest import Client

# ---------------- TWILIO CONFIG ----------------
account_sid = "AC92259d906b69e31281c79a550a7dbae7"
auth_token = "6b61d6273163663dab81c9cd2e36fbcf"

twilio_number = "+16066991935"      # no spaces
receiver_number = "+918318800363"   # no spaces

client = Client(account_sid, auth_token)

# ---------------- ALERT FUNCTION ----------------
def send_alert():
    lat, lon = 28.6139, 77.2090
    location_link = f"https://www.google.com/maps?q={lat},{lon}"

    try:
        message = client.messages.create(
            body=f"Driver Alert! Drowsiness detected.\nLocation: {location_link}",
            from_=twilio_number,
            to=receiver_number
        )
        print("SMS Sent Successfully")
        print("SID:", message.sid)

    except Exception as e:
        print("SMS Failed:", str(e))

# ---------------- SMART ACTION ----------------
def emergency_action():
    print("Emergency Mode Activated")
    print("Slowing down vehicle...")
    print("Hazard lights ON")

    for _ in range(4):
        winsound.Beep(1500, 400)


# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

count = 0
state = "Awake"
start_time = 0
alarm_on = 0
sms_sent = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    t1 = time.time()

    # -------- NIGHT VISION --------
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    faces = face.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        count += 1
        state = "Drowsy"

        if count == 1:
            start_time = time.time()

    else:
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            eyes = eye.detectMultiScale(roi_gray)

            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 1)

            if len(eyes) <= 1:
                count += 1
                state = "Drowsy"

                if count == 1:
                    start_time = time.time()
            else:
                count = 0
                state = "Awake"
                alarm_on = 0
                sms_sent = 0

    # -------- TRIGGER --------
    if count > 5:
        if alarm_on == 0:
            winsound.Beep(1200, 300)
            alarm_on = 1

        if sms_sent == 0:
            send_alert()
            emergency_action()
            sms_sent = 1

    # -------- TIME --------
    sleep_time = int(time.time() - start_time) if state == "Drowsy" else 0

    # -------- FPS --------
    t2 = time.time()
    fps = int(1 / (t2 - t1))

    # -------- DISPLAY --------
    color = (0, 0, 255) if state == "Drowsy" else (0, 255, 0)

    cv2.putText(frame, f"Status: {state}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.putText(frame, f"Sleep Time: {sleep_time}s", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, f"FPS: {fps}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("Drowsiness Monitor", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
