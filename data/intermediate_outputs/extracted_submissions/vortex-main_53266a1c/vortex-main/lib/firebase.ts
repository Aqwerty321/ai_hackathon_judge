// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore"; // Import Firestore
import { getAuth } from "firebase/auth"; // Import Firebase Authentication

const firebaseConfig = {
  apiKey: "AIzaSyDpvTrV2qJ4zhiFMyYvBWwSyrvlTXd1PlY",
  authDomain: "vortex-77060.firebaseapp.com",
  projectId: "vortex-77060",
  storageBucket: "vortex-77060.appspot.com",
  messagingSenderId: "832175265393",
  appId: "1:832175265393:web:0b0b2398525e60bd6fadd0",
  measurementId: "G-30KRN6G54Q",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app); // Initialize Firestore
const auth = getAuth(app); // Initialize Firebase Authentication

export { db, auth }; // Export Firestore and Auth for use in other parts of your application
