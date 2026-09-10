# Imazhi i frontend-it Next.js, i konfiguruar për zhvillim me
# hot-reload. Për prodhim do të përdorej një build shumë-fazësh me
# `next build` dhe `next start`.
FROM node:20-alpine

WORKDIR /app

# Varësitë instalohen para kodit, që ndryshimet e faqeve të mos e
# rindërtojnë këtë shtresë.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
