# Gráfica Rápida Mobile

App mobile Expo/React Native separado do Streamlit web.

## Arquitetura

- `app.py` continua sendo o app web em Streamlit.
- `mobile/` contém o app mobile Expo.
- O app mobile é offline e usa SQLite local no próprio celular.
- Não existe login no app mobile: o uso é de usuário único no aparelho.
- O app mobile não usa `DATABASE_URL`, `JWT_SECRET`, Supabase direto nem `localhost`.

## Rodar em desenvolvimento

```powershell
cd mobile
npm install
npm start
```

## Gerar APK

O app está configurado com o nome `Gráfica Rápida`, package Android `com.graficarapida.faturamento` e ícone em `mobile/assets/`.

Build local release:

```powershell
npx expo prebuild --platform android --clean --no-install
cd android
.\gradlew.bat assembleRelease --no-daemon
```

APK offline gerado nesta máquina:

```text
mobile/GraficaRapida-offline-release.apk
```

Evite instalar APK debug em celular comum. O APK debug pode depender do Metro rodando no computador.

## Backup Supabase

A importação dos dados atuais do Supabase para o SQLite local ainda será feita em uma etapa separada. A ideia recomendada é gerar um arquivo de backup contendo apenas os dados de faturamento necessários e importar esse arquivo no app mobile.
