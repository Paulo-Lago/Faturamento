# Faturamento Mobile

App mobile Expo/React Native separado do Streamlit web.

## Arquitetura

- `app.py` continua sendo o app web em Streamlit.
- `mobile_api.py` expõe uma API HTTP para o app mobile.
- `mobile/` contém o app mobile Expo.
- O app mobile não deve receber `DATABASE_URL`, `JWT_SECRET` ou qualquer segredo.

## Rodar a API mobile

Configure as variáveis no ambiente do servidor:

```powershell
$env:DATABASE_URL="postgresql://..."
$env:JWT_SECRET="..."
uvicorn mobile_api:app --host 0.0.0.0 --port 8000
```

## Rodar o app mobile

Crie um arquivo `.env` dentro de `mobile/` baseado em `.env.example`.

Para testar no celular físico, use o IP da máquina ou a URL pública da API:

```text
EXPO_PUBLIC_API_URL=http://SEU-IP-LOCAL:8000
```

Depois rode:

```powershell
cd mobile
npm install
npm start
```

Abra com o Expo Go ou gere builds nativos com EAS quando a API estiver publicada.

## Gerar APK

O app está configurado com o nome `Gráfica Rápida` e package Android `com.graficarapida.faturamento`.

Build em nuvem com EAS, quando estiver logado na conta Expo:

```powershell
npx eas-cli build --platform android --profile preview
```

Build local debug:

```powershell
npx expo prebuild --platform android --no-install
cd android
.\gradlew.bat assembleDebug --no-daemon
```

APK gerado nesta máquina:

```text
mobile/GraficaRapida-debug.apk
```
