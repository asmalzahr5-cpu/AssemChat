import google.generativeai as genai

# المفتاح الجديد الذي ينتهي بـ igMk
API_KEY = "ضـع_الـمفتاح_هـنا"
genai.configure(api_key=API_KEY)

# استخدام المكتبة الرسمية لاستدعاء الموديل
model = genai.GenerativeModel('gemini-1.5-flash')

print("🚀 AssemChat يعمل الآن بمكتبة Google الرسمية")

while True:
    user_input = input("\n👤 أنت: ")
    if user_input.lower() in ['exit', 'خروج']: break
    
    try:
        # هذا هو الأمر الخاص بمكتبة قوقل
        response = model.generate_content(user_input)
        print(f"\n🤖 Gemini: {response.text}")
    except Exception as e:
        print(f"⚠️ تنبيه: {e}")

