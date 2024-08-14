
# ARG NODE_VERSION=20.15.1
ARG PNPM_VERSION=9.6.0
# ARG PYTHON_VERSION=3.11.2

# Step 1: Build the frontend
FROM nikolaik/python-nodejs:python3.11-nodejs20

WORKDIR /home/pn/app
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Install pnpm
RUN npm install -g pnpm@${PNPM_VERSION}
RUN npm install -g serve

#Install wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    && apt-get clean


# Copy and install backend dependencies
COPY backend/requirements.txt /home/pn/app/backend/
RUN pip install --no-cache-dir -r /home/pn/app/backend/requirements.txt

# Copy the backend code into the container
COPY backend /home/pn/app/backend

# Install frontend dependencies and build the frontend
WORKDIR /home/pn/app/nextjs
COPY nextjs/package.json nextjs/pnpm-lock.yaml ./
RUN rm -rf node_modules

RUN pnpm install --frozen-lockfile
COPY nextjs/ ./
RUN pnpm run build

# Set environment variables
WORKDIR /home/pn/app

ENV NODE_ENV=production

ENV PYTHONPATH=/home/pn/app/backend

# Expose ports for both frontend and backend
EXPOSE 3000 8000
# Install serve to run the Next.js frontend
USER pn

# Start both the backend and frontend using a shell script
CMD ["sh", "-c", "uvicorn backend.api.test:app --host 0.0.0.0 --port 8000 & npm run next-dev --prefix nextjs"]