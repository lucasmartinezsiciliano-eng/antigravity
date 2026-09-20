# Node 22 trae ejecucion de TypeScript sin compilar, asi que no hay paso de
# build: lo que se lee en el repo es lo que corre en produccion.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

COPY src ./src

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080

# Sin root: si algun dia un adaptador procesa algo que no debe, que no sea como root.
USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||8080)+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "--experimental-strip-types", "src/index.ts"]
