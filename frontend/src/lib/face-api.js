

import * as faceapi from 'face-api.js';



let modelsLoaded = false;
let loadingPromise = null;

const MODEL_URL = '/models';



export const MATCH_THRESHOLD = 0.6;




export async function loadModels() {
  if (modelsLoaded) return true;
  if (loadingPromise) return loadingPromise;

  loadingPromise = (async () => {
    try {
      console.log('[FaceAPI] Loading models from', MODEL_URL, '...');
      await Promise.all([
        faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
      ]);
      modelsLoaded = true;
      console.log('[FaceAPI] ✅ All models loaded');
      return true;
    } catch (err) {
      console.error('[FaceAPI] ❌ Failed to load models:', err);
      loadingPromise = null; 
      throw err;
    }
  })();

  return loadingPromise;
}


export function isReady() {
  return modelsLoaded;
}




export async function detectFace(videoEl) {
  if (!modelsLoaded) {
    throw new Error('[FaceAPI] Models not loaded yet. Call loadModels() first.');
  }

  
  const inputSizes = [480, 640];

  for (const inputSize of inputSizes) {
    try {
      const options = new faceapi.SsdMobilenetv1Options({
        minConfidence: 0.5, 
        inputSize,
      });

      const detections = await faceapi
        .detectAllFaces(videoEl, options)
        .withFaceLandmarks()
        .withFaceDescriptors();

      if (detections && detections.length > 0) {
        
        let best = detections[0];
        let bestArea = 0;
        for (const d of detections) {
          const area = d.detection.box.width * d.detection.box.height;
          if (area > bestArea) {
            bestArea = area;
            best = d;
          }
        }
        console.log(`[FaceAPI] ✅ Found ${detections.length} face(s), picked largest (area=${Math.round(bestArea)})`);
        return best;
      }
    } catch (err) {
      console.warn(`[FaceAPI] Detection failed at inputSize=${inputSize}:`, err.message);
    }
  }

  return null;
}


export async function detectAllFaces(videoEl) {
  if (!modelsLoaded) {
    throw new Error('[FaceAPI] Models not loaded yet.');
  }

  return faceapi
    .detectAllFaces(videoEl)
    .withFaceLandmarks()
    .withFaceDescriptors();
}




export function findBestMatch(queryDescriptor, students) {
  if (!students || students.length === 0) {
    return { student: null, distance: Infinity, confidence: 0 };
  }

  
  let avgDescriptor = queryDescriptor;
  if (Array.isArray(queryDescriptor) && queryDescriptor.length > 0) {
    const n = queryDescriptor.length;
    const dim = queryDescriptor[0].length;
    avgDescriptor = new Float32Array(dim);
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < dim; j++) {
        avgDescriptor[j] += queryDescriptor[i][j];
      }
    }
    for (let j = 0; j < dim; j++) {
      avgDescriptor[j] /= n;
    }
    console.log(`[FaceAPI] Averaged ${n} descriptors for matching`);
  }

  
  const enrolled = students.filter((s) => s.descriptor && s.descriptor.length > 0);
  if (enrolled.length === 0) {
    return { student: null, distance: Infinity, confidence: 0 };
  }

  let bestMatch = null;
  let bestDistance = Infinity;

  for (const s of enrolled) {
    const desc = s.descriptor instanceof Float32Array
      ? s.descriptor
      : new Float32Array(s.descriptor);

    const dist = faceapi.euclideanDistance(avgDescriptor, desc);
    if (dist < bestDistance) {
      bestDistance = dist;
      bestMatch = s;
    }
  }

  
  const confidence = Math.max(0, Math.round((1 - bestDistance / (MATCH_THRESHOLD * 2)) * 100));
  const isMatch = bestDistance <= MATCH_THRESHOLD;

  return {
    student: isMatch ? bestMatch : null,
    distance: bestDistance,
    confidence: isMatch ? confidence : 0,
  };
}




export function parseDescriptor(raw) {
  if (!raw) return null;
  if (raw instanceof Float32Array) return raw;
  if (Array.isArray(raw)) return new Float32Array(raw);
  if (typeof raw === 'string') {
    try {
      return new Float32Array(JSON.parse(raw));
    } catch {
      return null;
    }
  }
  return null;
}


export function serializeDescriptor(desc) {
  if (!desc) return null;
  return Array.from(desc); 
}
