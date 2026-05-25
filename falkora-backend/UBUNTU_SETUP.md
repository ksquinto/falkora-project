# 🐧 Instalación del Script de Essentia en Ubuntu

Este script permite a Windows llamar a Essentia en Ubuntu WSL2 para extraer features de WAVs.

## Paso 1: Copiar el script a Ubuntu

Desde tu terminal **Ubuntu** (WSL2), corre:

```bash
cd ~/falkora-essentia
cat > extract_single_wav.py << 'SCRIPT_END'
```

**Ahora pega todo el contenido del archivo `extract_single_wav.py` que está en el backend**, y luego presiona Enter y escribe:

```bash
SCRIPT_END
```

O más fácil: **copia el archivo desde Windows a Ubuntu**:

Desde PowerShell:
```powershell
# Copiar el script al entorno de Ubuntu
copy "C:\Users\ksqr9\OneDrive\Falkora project\falkora-backend\extract_single_wav.py" \\wsl$\Ubuntu\home\ksqr98\falkora-essentia\
```

## Paso 2: Hacer el script ejecutable

En Ubuntu:
```bash
cd ~/falkora-essentia
chmod +x extract_single_wav.py
```

## Paso 3: Probar que funciona

```bash
# Activar entorno
source ~/falkora-essentia/venv/bin/activate

# Probar con un WAV de ejemplo
# (suponiendo que tienes test.wav en la carpeta)
python extract_single_wav.py test.wav
```

Deberías ver un JSON con todas las features.

## Paso 4: Verificar que Windows puede llamarlo

Desde PowerShell (Windows):
```powershell
wsl ~/falkora-essentia/venv/bin/python ~/falkora-essentia/extract_single_wav.py "/mnt/c/Users/ksqr9/OneDrive/Falkora project/test.wav"
```

Si ves JSON con las features → ✅ todo funciona.

## Solución de problemas

**"wsl: command not found"**
→ WSL2 no está instalado o no está en el PATH de Windows.

**"No such file or directory"**
→ Verifica las rutas. Recuerda que desde Windows las rutas de Ubuntu son `~/...` y desde Ubuntu las rutas de Windows son `/mnt/c/...`

**"ModuleNotFoundError: No module named 'essentia'"**
→ El entorno virtual no está activado. El backend llama directamente al python del venv: `~/falkora-essentia/venv/bin/python`

---

Una vez que esto funcione, el backend de Falkora puede procesar WAVs automáticamente.
