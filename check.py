try:
    import google.generativeai as genai
    import pydantic_core
    print("🚀 مبروك يا عاصم! المكتبة تعمل بنجاح تام")
    print(f"إصدار التشفير: {pydantic_core.__version__}")
except ImportError as e:
    print(f"❌ لا يزال هناك نقص: {e}")
except Exception as e:
    print(f"⚠️ حدث خطأ غير متوقع: {e}")

