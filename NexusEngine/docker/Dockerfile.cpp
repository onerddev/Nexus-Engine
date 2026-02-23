# Dockerfile for C++ Build Environment
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++-12 \
    clang-15 \
    git \
    wget \
    libboost-all-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY cpp/ cpp/
COPY CMakeLists.txt .

RUN mkdir build && cd build && \
    cmake -DCMAKE_CXX_COMPILER=g++-12 -DCMAKE_BUILD_TYPE=Release .. && \
    make -j$(nproc)

# Final stage
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libgomp1 \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=0 /app/build /usr/local/nexus/
