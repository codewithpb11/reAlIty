import React, { useState, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StatusBar,
  Dimensions,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';

// ─── CONFIG: Set your deployed API URL here ───
const API_URL = 'https://192.168.0.101:8080';  // <-- CHANGE THIS after deploying
// const API_URL = 'http://192.168.0.101:8080';    // <-- For local testing on same WiFi

const { width } = Dimensions.get('window');

export default function App() {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const pickImage = useCallback(async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow access to photos.');
      return;
    }

    const pickerResult = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.9,
    });

    if (!pickerResult.canceled && pickerResult.assets?.length > 0) {
      setImage(pickerResult.assets[0]);
      setResult(null);
      setError(null);
    }
  }, []);

  const takePhoto = useCallback(async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow access to camera.');
      return;
    }

    const pickerResult = await ImagePicker.launchCameraAsync({
      allowsEditing: false,
      quality: 0.9,
    });

    if (!pickerResult.canceled && pickerResult.assets?.length > 0) {
      setImage(pickerResult.assets[0]);
      setResult(null);
      setError(null);
    }
  }, []);

  const analyzeImage = useCallback(async () => {
    if (!image) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: image.uri,
        name: image.fileName || 'image.jpg',
        type: image.mimeType || 'image/jpeg',
      });

      const response = await fetch(`${API_URL}/detect`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.error || 'Analysis failed');
      }

      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Something went wrong. Check your API_URL.');
    } finally {
      setLoading(false);
    }
  }, [image]);

  const clearAll = useCallback(() => {
    setImage(null);
    setResult(null);
    setError(null);
  }, []);

  const aiScore = result?.ai ?? 0;
  const humanScore = result?.hum ?? 0;
  const isAI = aiScore > humanScore;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.logo}>reAlIty</Text>
          <Text style={styles.tagline}>AI or Not? Find out.</Text>
        </View>

        {/* Image Preview */}
        {image ? (
          <View style={styles.previewCard}>
            <Image source={{ uri: image.uri }} style={styles.previewImage} />
            <Text style={styles.filename} numberOfLines={1}>
              {image.fileName || 'Selected image'}
            </Text>
          </View>
        ) : (
          <View style={styles.uploadZone}>
            <Text style={styles.uploadText}>Select an image to analyze</Text>
            <Text style={styles.uploadSub}>JPG, PNG, WEBP supported</Text>
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.btnSecondary} onPress={pickImage}>
            <Text style={styles.btnSecondaryText}>Gallery</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.btnSecondary} onPress={takePhoto}>
            <Text style={styles.btnSecondaryText}>Camera</Text>
          </TouchableOpacity>
        </View>

        {image && (
          <TouchableOpacity
            style={[styles.btnPrimary, loading && styles.btnDisabled]}
            onPress={analyzeImage}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#000" />
            ) : (
              <Text style={styles.btnPrimaryText}>Analyze</Text>
            )}
          </TouchableOpacity>
        )}

        {/* Error */}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Result */}
        {result && (
          <View style={styles.resultCard}>
            <Text style={[styles.verdict, isAI ? styles.verdictAI : styles.verdictHuman]}>
              {isAI ? 'Likely AI-Generated' : 'Likely Human-Made'}
            </Text>

            {/* AI Score */}
            <View style={styles.scoreRow}>
              <Text style={styles.scoreLabel}>AI-Generated</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, styles.barAI, { width: `${aiScore}%` }]} />
              </View>
              <Text style={styles.scoreValue}>{aiScore}%</Text>
            </View>

            {/* Human Score */}
            <View style={styles.scoreRow}>
              <Text style={styles.scoreLabel}>Human-Made</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, styles.barHuman, { width: `${humanScore}%` }]} />
              </View>
              <Text style={styles.scoreValue}>{humanScore}%</Text>
            </View>

            {/* Warning */}
            {result.overlay_detected && (
              <View style={styles.warningBox}>
                <Text style={styles.warningText}>
                  Heavy text or graphic overlays detected — treat this result with extra caution.
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Clear */}
        {(image || result || error) && (
          <TouchableOpacity style={styles.btnClear} onPress={clearAll}>
            <Text style={styles.btnClearText}>Clear</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0d0d0d',
  },
  scroll: {
    padding: 20,
    paddingBottom: 40,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 24,
  },
  logo: {
    fontSize: 36,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: 14,
    color: '#8a8a8a',
    marginTop: 4,
  },
  uploadZone: {
    width: width - 40,
    height: 220,
    borderWidth: 2,
    borderColor: '#333',
    borderStyle: 'dashed',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  uploadText: {
    fontSize: 16,
    color: '#f5f5f5',
    fontWeight: '500',
  },
  uploadSub: {
    fontSize: 12,
    color: '#8a8a8a',
    marginTop: 6,
  },
  previewCard: {
    width: width - 40,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
  },
  previewImage: {
    width: '100%',
    height: 260,
    resizeMode: 'cover',
  },
  filename: {
    padding: 12,
    color: '#f5f5f5',
    fontSize: 13,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
    marginBottom: 12,
  },
  btnSecondary: {
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#fff',
    backgroundColor: 'transparent',
  },
  btnSecondaryText: {
    color: '#f5f5f5',
    fontSize: 14,
    fontWeight: '500',
  },
  btnPrimary: {
    width: width - 40,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    marginTop: 4,
  },
  btnPrimaryText: {
    color: '#000000',
    fontSize: 15,
    fontWeight: '600',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  errorBox: {
    marginTop: 16,
    padding: 14,
    borderRadius: 10,
    backgroundColor: 'rgba(255,85,85,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255,85,85,0.25)',
    width: width - 40,
  },
  errorText: {
    color: '#ff5555',
    fontSize: 13,
  },
  resultCard: {
    width: width - 40,
    marginTop: 20,
    padding: 20,
    borderRadius: 16,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
  },
  verdict: {
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 16,
  },
  verdictAI: {
    color: '#ff5555',
  },
  verdictHuman: {
    color: '#55ff88',
  },
  scoreRow: {
    marginBottom: 14,
  },
  scoreLabel: {
    fontSize: 12,
    color: '#8a8a8a',
    fontWeight: '500',
    marginBottom: 6,
  },
  barBg: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  barAI: {
    backgroundColor: '#ff5555',
  },
  barHuman: {
    backgroundColor: '#55ff88',
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f5f5f5',
    marginTop: 4,
  },
  warningBox: {
    marginTop: 10,
    padding: 12,
    borderRadius: 10,
    backgroundColor: 'rgba(255,170,68,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,170,68,0.2)',
  },
  warningText: {
    color: '#ffaa44',
    fontSize: 12,
    fontStyle: 'italic',
  },
  btnClear: {
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 32,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
  },
  btnClearText: {
    color: '#8a8a8a',
    fontSize: 13,
  },
});
