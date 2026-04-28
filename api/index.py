from app import app

# Função handler para Vercel
def handler(request):
    return app(request)
