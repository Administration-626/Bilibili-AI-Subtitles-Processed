import speech_recognition as sr

r = sr.Recognizer()
with sr.AudioFile("local_file/xiaofan_voice_reference.wav") as source:
    audio = r.record(source)

try:
    text = r.recognize_google(audio, language="zh-CN")
    print(text)
except Exception as e:
    print("Error:", e)
