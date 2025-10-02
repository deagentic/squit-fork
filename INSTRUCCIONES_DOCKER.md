# 🐳 Instrucciones para Ejecutar SQUIT con Docker

**IMPORTANTE: Leer antes de ejecutar**

---

## ⚡ Pasos para Primera Ejecución

### 1. Limpiar Imágenes Viejas (Si existen)

```bash
make squit-clean
```

### 2. Reconstruir Imagen (Sin cache)

```bash
make squit-rebuild
```

**Esto tomará ~1-2 minutos y:**
- Construye imagen con google-adk 1.15.1 ✅
- Instala deprecated 1.2.18 ✅
- Instala todas las dependencias compatibles ✅
- Limpia contenedores viejos automáticamente ✅

### 3. Usar el Sistema

Una vez construida la imagen, simplemente:

```bash
make squit
```

---

## 📋 Troubleshooting

### Error: "No module named 'deprecated'"

**Causa:** Imagen vieja en cache

**Solución:**
```bash
make squit-clean
make squit-rebuild
```

### Error: "No module named 'google.adk.apps'"

**Causa:** google-adk versión 0.5.0 (vieja)

**Solución:**
```bash
# Verificar requirements.txt tiene:
grep "google-adk" requirements.txt
# Debe decir: google-adk>=1.15.0

# Rebuild completo
make squit-rebuild
```

### Verificar Dependencias en la Imagen

```bash
docker run --rm squit-squit-cli:latest python3 -c "
import google.adk
print(f'google-adk: {google.adk.__version__}')
import deprecated
print(f'deprecated: {deprecated.__version__}')
print('✅ Dependencias correctas')
"
```

Debe mostrar:
```
google-adk: 1.15.1
deprecated: 1.2.18
✅ Dependencias correctas
```

---

## 🔧 Comandos Disponibles

| Comando | Propósito | Cuándo Usar |
|---------|-----------|-------------|
| `make squit-clean` | Limpiar todo | Cuando hay problemas |
| `make squit-rebuild` | Rebuild completo | Primera vez o después de limpiar |
| `make squit-build` | Solo construir | Para actualizar imagen |
| `make squit` | Ejecutar CLI | Uso normal |

---

## ✅ Checklist

- [ ] Docker Desktop corriendo
- [ ] Ejecutar `make squit-clean`
- [ ] Ejecutar `make squit-rebuild`
- [ ] Esperar build (~1-2 min)
- [ ] Ejecutar `make squit` para usar

---

## 📊 Dependencias Instaladas en Imagen

```
✅ google-adk: 1.15.1
✅ google-genai: 1.40.0
✅ google-cloud-bigquery: 3.38.0
✅ deprecated: 1.2.18
✅ deprecation: 2.1.0
✅ weaviate-client: 4.17.0
✅ langchain-core: 0.3.77
✅ pandas: 2.3.3
✅ + 80 dependencias más
```

---

**Última actualización:** 2025-10-02  
**Autor:** Karim Touma

