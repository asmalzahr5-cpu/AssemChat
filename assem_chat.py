import google.generativeai as genai

# مفتاحك الصحيح
API_KEY = "AIzaSyDWuIiPxbY6woCTYzBX4_yNtv0CgHKnu3M"
genai.configure(api_key=API_KEY)

def start_chat():
    print("="*30)
    print("   AssemChat Project v1.0   ")
    print("="*30)
    
    # قائمة بأسماء النماذج المحتملة حسب تحديثات جوجل الأخيرة
    model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    model = None
    for name in model_names:
        try:
            test_model = genai.GenerativeModel(name)
            # تجربة إرسال طلب بسيط جداً للتأكد من وجود النموذج
            test_model.generate_content("Hi", generation_config={"max_output_tokens": 1})
            model = test_model
            print(f"✅ تم الاتصال بنجاح عبر نموذج: {name}")
            break
        except Exception:
            continue

    if not model:
        print("❌ فشل العثور على نموذج متوافق. جاري محاولة الاتصال المباشر...")
        model = genai.GenerativeModel('models/gemini-1.5-flash')

    print("\n[نظام]: اكتب 'خروج' للإنهاء.\n")

    while True:
        user_input = input("👤 أنت: ")
        
        if user_input.lower() in ['خروج', 'exit', 'quit']:
            print("👋 مع السلامة يا عاصم!")
            break

        try:
            # طلب الرد
            response = model.generate_content(user_input)
            print(f"\n🤖 Gemini: {response.text}\n")
            print("-" * 20)
        except Exception as e:
            print(f"\n⚠️ خطأ في الرد: {e}")

if __name__ == "__main__":
    start_chat()

