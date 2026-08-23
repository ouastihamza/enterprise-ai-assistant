"use client";

import {
  useEffect,
  useRef,
} from "react";

import * as THREE from "three";

interface ParticleSphereProps {
  className?: string;
}

const PARTICLE_COUNT = 22_000;

const vertexShader = `
  attribute float aSize;
  attribute float aRandom;

  uniform float uTime;
  uniform float uPixelRatio;
  uniform vec2 uPointer;

  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    vec3 animatedPosition = position;

    float waveOne =
      sin(
        position.y * 5.0 +
        position.x * 3.0 +
        uTime * 0.55 +
        aRandom * 4.0
      ) * 0.014;

    float waveTwo =
      cos(
        position.z * 6.0 -
        position.y * 2.0 +
        uTime * 0.42
      ) * 0.009;

    vec3 normalDirection =
      normalize(position);

    animatedPosition +=
      normalDirection *
      (waveOne + waveTwo);

    animatedPosition.x +=
      uPointer.x *
      0.035 *
      (1.0 + position.z);

    animatedPosition.y -=
      uPointer.y *
      0.025 *
      (1.0 + position.z);

    vec4 modelPosition =
      modelMatrix *
      vec4(
        animatedPosition,
        1.0
      );

    vec4 viewPosition =
      viewMatrix *
      modelPosition;

    gl_Position =
      projectionMatrix *
      viewPosition;

    float perspective =
      1.0 /
      max(
        0.4,
        -viewPosition.z
      );

    gl_PointSize =
      aSize *
      uPixelRatio *
      perspective *
      3.8;

    float depth =
      smoothstep(
        -2.0,
        2.0,
        viewPosition.z
      );

    vAlpha =
      mix(
        0.38,
        1.0,
        depth
      );

    vColor = color;
  }
`;

const fragmentShader = `
  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    vec2 centeredPoint =
      gl_PointCoord -
      vec2(0.5);

    float distanceToCenter =
      length(centeredPoint);

    float core =
      1.0 -
      smoothstep(
        0.0,
        0.24,
        distanceToCenter
      );

    float glow =
      1.0 -
      smoothstep(
        0.12,
        0.5,
        distanceToCenter
      );

    float alpha =
      core * 0.84 +
      glow * 0.22;

    if (alpha < 0.025) {
      discard;
    }

    gl_FragColor =
      vec4(
        vColor,
        alpha * vAlpha
      );
  }
`;

function createSphereGeometry():
  THREE.BufferGeometry {
  const positions =
    new Float32Array(
      PARTICLE_COUNT * 3
    );

  const colors =
    new Float32Array(
      PARTICLE_COUNT * 3
    );

  const sizes =
    new Float32Array(
      PARTICLE_COUNT
    );

  const randomValues =
    new Float32Array(
      PARTICLE_COUNT
    );

  const turquoise =
    new THREE.Color("#20e0dc");

  const cyan =
    new THREE.Color("#7df4ff");

  const blue =
    new THREE.Color("#208eff");

  const deepBlue =
    new THREE.Color("#0755ca");

  const white =
    new THREE.Color("#efffff");

  const mixedColor =
    new THREE.Color();

  const goldenAngle =
    Math.PI *
    (3 - Math.sqrt(5));

  for (
    let index = 0;
    index < PARTICLE_COUNT;
    index += 1
  ) {
    const positionIndex =
      index * 3;

    const normalizedIndex =
      index /
      Math.max(
        PARTICLE_COUNT - 1,
        1
      );

    const y =
      1 -
      normalizedIndex * 2;

    const radiusAtY =
      Math.sqrt(
        Math.max(
          0,
          1 - y * y
        )
      );

    const theta =
      goldenAngle * index;

    const surfaceNoise =
      (Math.random() - 0.5) *
      0.085;

    const radius =
      1.34 +
      surfaceNoise;

    const x =
      Math.cos(theta) *
      radiusAtY *
      radius;

    const z =
      Math.sin(theta) *
      radiusAtY *
      radius;

    positions[positionIndex] = x;

    positions[
      positionIndex + 1
    ] =
      y * radius;

    positions[
      positionIndex + 2
    ] = z;

    const verticalMix =
      THREE.MathUtils.clamp(
        (y + 1) / 2,
        0,
        1
      );

    const horizontalMix =
      THREE.MathUtils.clamp(
        (x / radius + 1) / 2,
        0,
        1
      );

    const depthMix =
      THREE.MathUtils.clamp(
        (z / radius + 1) / 2,
        0,
        1
      );

    if (verticalMix > 0.78) {
      mixedColor
        .copy(white)
        .lerp(
          cyan,
          0.6
        );
    } else if (
      horizontalMix > 0.52
    ) {
      mixedColor
        .copy(turquoise)
        .lerp(
          cyan,
          depthMix * 0.65
        );
    } else {
      mixedColor
        .copy(blue)
        .lerp(
          deepBlue,
          1 - depthMix
        );
    }

    const brightness =
      0.82 +
      Math.random() * 0.32;

    mixedColor.multiplyScalar(
      brightness
    );

    colors[positionIndex] =
      mixedColor.r;

    colors[
      positionIndex + 1
    ] =
      mixedColor.g;

    colors[
      positionIndex + 2
    ] =
      mixedColor.b;

    sizes[index] =
      1.6 +
      Math.random() * 2.8;

    randomValues[index] =
      Math.random();
  }

  const geometry =
    new THREE.BufferGeometry();

  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(
      positions,
      3
    )
  );

  geometry.setAttribute(
    "color",
    new THREE.BufferAttribute(
      colors,
      3
    )
  );

  geometry.setAttribute(
    "aSize",
    new THREE.BufferAttribute(
      sizes,
      1
    )
  );

  geometry.setAttribute(
    "aRandom",
    new THREE.BufferAttribute(
      randomValues,
      1
    )
  );

  geometry.computeBoundingSphere();

  return geometry;
}

function getCameraDistance(
  width: number
): number {
  if (width < 480) {
    return 7.6;
  }

  if (width < 700) {
    return 7.1;
  }

  if (width < 1000) {
    return 6.55;
  }

  return 6.2;
}

export function ParticleSphere({
  className = "",
}: ParticleSphereProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  useEffect(() => {
    const currentContainer =
      containerRef.current;

    if (currentContainer === null) {
      return;
    }

    const containerElement:
      HTMLDivElement =
        currentContainer;

    const scene =
      new THREE.Scene();

    const camera =
      new THREE.PerspectiveCamera(
        40,
        1,
        0.1,
        100
      );

    camera.position.set(
      0,
      0,
      6.2
    );

    const renderer =
      new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference:
          "high-performance",
      });

    renderer.setClearColor(
      0x000000,
      0
    );

    const pixelRatio =
      Math.min(
        window.devicePixelRatio,
        2
      );

    renderer.setPixelRatio(
      pixelRatio
    );

    renderer.outputColorSpace =
      THREE.SRGBColorSpace;

    renderer.domElement.setAttribute(
      "aria-hidden",
      "true"
    );

    renderer.domElement.style.display =
      "block";

    renderer.domElement.style.width =
      "100%";

    renderer.domElement.style.height =
      "100%";

    renderer.domElement.style.maxWidth =
      "100%";

    containerElement.appendChild(
      renderer.domElement
    );

    const geometry =
      createSphereGeometry();

    const material =
      new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        vertexColors: true,
        blending:
          THREE.AdditiveBlending,
        uniforms: {
          uTime: {
            value: 0,
          },
          uPixelRatio: {
            value:
              pixelRatio,
          },
          uPointer: {
            value:
              new THREE.Vector2(
                0,
                0
              ),
          },
        },
        vertexShader,
        fragmentShader,
      });

    const particleSphere =
      new THREE.Points(
        geometry,
        material
      );

    particleSphere.rotation.x =
      -0.12;

    particleSphere.rotation.z =
      0.08;

    scene.add(
      particleSphere
    );

    const atmosphericGeometry =
      new THREE.SphereGeometry(
        1.43,
        64,
        64
      );

    const atmosphericMaterial =
      new THREE.MeshBasicMaterial({
        color: "#32dce0",
        transparent: true,
        opacity: 0.025,
        side: THREE.BackSide,
        depthWrite: false,
      });

    const atmosphere =
      new THREE.Mesh(
        atmosphericGeometry,
        atmosphericMaterial
      );

    scene.add(atmosphere);

    const pointerTarget =
      new THREE.Vector2(
        0,
        0
      );

    const pointerCurrent =
      new THREE.Vector2(
        0,
        0
      );

    let targetRotationX = 0;
    let targetRotationY = 0;

    let currentRotationX = 0;
    let currentRotationY = 0;

    function updatePointer(
      event: PointerEvent
    ): void {
      const bounds =
        containerElement
          .getBoundingClientRect();

      if (
        bounds.width <= 0 ||
        bounds.height <= 0
      ) {
        return;
      }

      const x =
        ((event.clientX -
          bounds.left) /
          bounds.width) *
          2 -
        1;

      const y =
        ((event.clientY -
          bounds.top) /
          bounds.height) *
          2 -
        1;

      pointerTarget.set(
        x,
        -y
      );

      targetRotationY =
        x * 0.32;

      targetRotationX =
        y * 0.18;
    }

    function resetPointer(): void {
      pointerTarget.set(
        0,
        0
      );

      targetRotationX = 0;
      targetRotationY = 0;
    }

    function updateRendererSize():
      void {
      const width =
        containerElement.clientWidth;

      const height =
        containerElement.clientHeight;

      if (
        width <= 0 ||
        height <= 0
      ) {
        return;
      }

      renderer.setSize(
        width,
        height,
        false
      );

      camera.aspect =
        width / height;

      camera.position.z =
        getCameraDistance(
          width
        );

      camera.updateProjectionMatrix();
    }

    containerElement.addEventListener(
      "pointermove",
      updatePointer
    );

    containerElement.addEventListener(
      "pointerleave",
      resetPointer
    );

    const resizeObserver =
      new ResizeObserver(() => {
        updateRendererSize();
      });

    resizeObserver.observe(
      containerElement
    );

    updateRendererSize();

    const clock =
      new THREE.Clock();

    let animationFrameId = 0;

    function renderFrame(): void {
      const elapsedTime =
        clock.getElapsedTime();

      pointerCurrent.lerp(
        pointerTarget,
        0.045
      );

      currentRotationX =
        THREE.MathUtils.lerp(
          currentRotationX,
          targetRotationX,
          0.035
        );

      currentRotationY =
        THREE.MathUtils.lerp(
          currentRotationY,
          targetRotationY,
          0.035
        );

      material.uniforms.uTime.value =
        elapsedTime;

      material.uniforms.uPointer.value.copy(
        pointerCurrent
      );

      particleSphere.rotation.x =
        -0.12 +
        currentRotationX;

      particleSphere.rotation.y =
        elapsedTime * 0.105 +
        currentRotationY;

      particleSphere.rotation.z =
        0.08 +
        Math.sin(
          elapsedTime * 0.25
        ) *
          0.025;

      particleSphere.position.y =
        Math.sin(
          elapsedTime * 0.52
        ) *
        0.045;

      particleSphere.scale.setScalar(
        1 +
          Math.sin(
            elapsedTime * 0.42
          ) *
            0.01
      );

      atmosphere.rotation.y =
        -elapsedTime * 0.025;

      atmosphere.rotation.x =
        currentRotationX * 0.4;

      renderer.render(
        scene,
        camera
      );

      animationFrameId =
        window.requestAnimationFrame(
          renderFrame
        );
    }

    renderFrame();

    return () => {
      window.cancelAnimationFrame(
        animationFrameId
      );

      resizeObserver.disconnect();

      containerElement.removeEventListener(
        "pointermove",
        updatePointer
      );

      containerElement.removeEventListener(
        "pointerleave",
        resetPointer
      );

      scene.remove(
        particleSphere
      );

      scene.remove(
        atmosphere
      );

      geometry.dispose();
      material.dispose();

      atmosphericGeometry.dispose();
      atmosphericMaterial.dispose();

      renderer.dispose();

      if (
        renderer.domElement
          .parentElement ===
        containerElement
      ) {
        containerElement.removeChild(
          renderer.domElement
        );
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={[
        "particle-sphere",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden="true"
    />
  );
}