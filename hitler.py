import cv2
import pyautogui as gui
import mediapipe as mp
import speech_recognition as sr
import pyttsx3
import time
import threading

# Initialize MediaPipe Hand model
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_tracking_confidence=0.8, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# Initialize voice recognizer and speech engine
recogn = sr.Recognizer()
engine = pyttsx3.init()

# Initialize the webcam
cam = cv2.VideoCapture(0)

class GestureController:
    def __init__(self):
        # Set initial mode and gesture variables
        self.current_mode = None  # "slide" or "document"
        self.last_gesture = None  # Last detected gesture
        self.gesture_time = 0  # Timestamp of last gesture detection
        self.auto_mode = False
        self.auto_delay = 0

        # Prompt user to select mode
        print("\t\tSelect mode:\n\
              -------------\n\
              1. Slide Presentation\n\
              2. Document Navigation")

        option = input("\t\tEnter option: ")

        # Set mode based on user input
        if option == "1":
            self.current_mode = "slide"
        elif option == "2":
            self.current_mode = "document"
        else:
            print("Invalid choice. Exiting...")
            exit()

    @staticmethod
    def detect_gesture(landmarks, handedness, mode):
        # Extract key points from hand landmarks
        wrist = landmarks[0]
        index = landmarks[8]
        middle = landmarks[12]
        ring = landmarks[16]
        pinky = landmarks[20]
        thumb = landmarks[4]

        if mode is not None:
            # Gesture: Voice Command (Index and middle fingers up)
            if index.y < landmarks[7].y and middle.y < landmarks[11].y and ring.y > landmarks[13].y and pinky.y > landmarks[17].y:
                if index.y < wrist.y and middle.y < wrist.y:
                    return "voice"

            if mode == "slide":
                # Gesture: Next Slide (Right hand pointing to the right)
                if wrist.y < index.y and handedness == "Right":
                    if index.x > landmarks[7].x:
                        if not (middle.x > landmarks[11].x or ring.x > landmarks[15].x or pinky.x > landmarks[19].x):
                            return "next"

                # Gesture: Previous Slide (Left hand pointing to the left)
                elif wrist.y < index.y and handedness == "Left":
                    if index.x < landmarks[7].x:
                        if not (middle.x < landmarks[11].x or ring.x < landmarks[15].x or pinky.x < landmarks[19].x):
                            return "prev"

            elif mode == "document":
                # Gesture: Scroll Up (Index up, others down)
                if index.y < wrist.y:
                    if index.y < landmarks[7].y and not (middle.y < landmarks[9].y or ring.y < landmarks[13].y or pinky.y < landmarks[17].y):
                        return "up"

                # Gesture: Scroll Down (Index and Middle up, others down)
                if index.y > wrist.y:
                    if index.y > landmarks[7].y and not (middle.y > landmarks[11].y or ring.y > landmarks[15].y or pinky.y > landmarks[19].y):
                        return "down"

                # Gesture: Pinch Zoom In (Thumb and index finger close together)
                if abs(thumb.x - index.x) < 0.05 and abs(thumb.y - index.y) < 0.05:
                    return "zoom_in"

                # Gesture: Pinch Zoom Out (Thumb and index finger far apart)
                if abs(thumb.x - index.x) > 0.1 and abs(thumb.y - index.y) > 0.1:
                    return "zoom_out"

        return None

    def execute_action(self, action):
        # Perform actions based on detected gesture
        if self.current_mode == "slide":
            if action == "next":
                gui.press("right")
                print("Next Slide")

            elif action == "prev":
                gui.press("left")
                print("Previous Slide")

            elif action == "voice":
                self.handle_voice_command()

        elif self.current_mode == "document":
            if action == "up":
                gui.scroll(250)
                print("Scrolling Up")

            elif action == "down":
                gui.scroll(-250)
                print("Scrolling Down")

            elif action == "voice":
                self.handle_voice_command()

            elif action == "zoom_in":
                gui.hotkey('ctrl', '+')
                print("Zooming In")

            elif action == "zoom_out":
                gui.hotkey('ctrl', '-')
                print("Zooming Out")

    def speak(self, audio):
        # Convert text to speech
        engine.say(audio)
        engine.runAndWait()

    def read_voice_command(self):
        # Listen for voice commands
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recogn.listen(source)
                print("Recognizing...")
                command = recogn.recognize_google(audio)
                print(f"Command: {command}")
                return command.lower()
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand that.")
                self.speak("I couldn't understand your command. Please try again.")
                return ""
            except sr.RequestError as e:
                print(f"Network error: {e}")
                self.speak("There seems to be a network issue. Please check your connection.")
                return ""

    def handle_voice_command(self):
        # Handle voice commands
        self.speak("Voice command mode activated. Say 'exit' to return.")
        self.speak("You can enable automatic slide navigation by saying 'Auto Mode'.")
        
        while True:
            command = self.read_voice_command()
            if command:  
                if "exit" in command:
                    self.speak("Exiting voice command mode.")
                    break

                if "current mode" in command:
                    self.speak(f"The current mode is {self.current_mode}.")

                if "change mode" in command:
                    if self.current_mode == "slide":
                        self.speak("Changing mode to document.")
                        self.current_mode = "document"
                    else:
                        self.speak("Changing mode to slide.")
                        self.current_mode = "slide"

                if self.current_mode == "slide":
                    if "next slide" in command:
                        gui.press("right")
                        print("Next Slide")

                    if "previous slide" in command:
                        gui.press("left")
                        print("Previous Slide")

                    if "auto mode" in command:
                        self.speak("Enabling automatic mode.")
                        try:
                            delay_time = 10
                            self.auto_mode = True
                            self.auto_delay = delay_time
                            threading.Thread(target=self.auto_slide_navigation).start()
                        except ValueError:
                            self.speak("Invalid delay time. Please try again.")

                    if "stop auto mode" in command:
                        self.auto_mode = False
                        self.speak("Automatic mode disabled.")

                    if "go to page" in command:
                        try:
                            page_number = int(command.split()[-1])
                            for _ in range(page_number):
                                gui.press("right")
                            print(f"Going to page {page_number}")
                        except ValueError:
                            self.speak("Invalid page number. Please try again.")

                if self.current_mode == "document":
                    if "scroll up" in command:
                        gui.scroll(250)
                        print("scrolling")
                    
                    if "scroll down" in command:
                        gui.scroll(-250)
                        print("scrolling")

                    if "zoom in" in command:
                        gui.hotkey('ctrl', '+')
                        print("Zooming In")

                    if "zoom out" in command:
                        gui.hotkey('ctrl', '-')
                        print("Zooming Out")

                    if "close document" in command:
                        gui.hotkey('ctrl', 'w')
                        print("Closing Document")

            else:
                self.speak("Exiting")
                break

    def auto_slide_navigation(self):
        # Automatically navigate slides
        while self.auto_mode:
            gui.press("right")
            print("Auto: Next Slide")
            time.sleep(self.auto_delay)

    def run(self):
        # Main loop to process webcam frames and detect gestures
        try:
            while True:
                ret, frame = cam.read()
                if not ret:
                    print("Unable to access camera. Exiting...")
                    break

                # Flip and process the frame
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        # Detect handedness ("Left" or "Right")
                        hand_label = handedness.classification[0].label

                        # Detect gesture
                        detected_gesture = self.detect_gesture(hand_landmarks.landmark, hand_label, self.current_mode)

                        # Confirm gesture with delay
                        current_time = time.time()
                        if detected_gesture == self.last_gesture:
                            if current_time - self.gesture_time >= 0.5:  # Gesture confirmed after 0.5 seconds
                                self.execute_action(detected_gesture)
                                self.gesture_time = current_time  # Reset time to prevent repeated execution
                        else:
                            self.last_gesture = detected_gesture
                            self.gesture_time = current_time

                # Display the frame
                cv2.imshow("Gesture Control", frame)

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cam.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = GestureController()
    controller.run()
