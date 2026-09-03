import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';

interface OptimizerModalProps {
  visible: boolean;
  onClose: () => void;
  isLoading: boolean;
  optimizedData: any;
  color: string;
}

export default function BasketOptimizerModal({ visible, onClose, isLoading, optimizedData, color }: OptimizerModalProps) {
  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.modalContent}>
          
          <View style={styles.header}>
            <Text style={styles.title}>✨ AI Cart Optimizer</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Text style={styles.closeText}>Close</Text>
            </TouchableOpacity>
          </View>

          {isLoading ? (
            <View style={styles.loadingState}>
              <ActivityIndicator size="large" color={color} />
              <Text style={styles.loadingText}>Calculating 100+ mathematical permutations...</Text>
            </View>
          ) : optimizedData ? (
            <ScrollView style={styles.scrollArea}>
              
              <View style={styles.recommendationBox}>
                <Text style={styles.recommendationText}>{optimizedData.recommendation}</Text>
              </View>

              {Object.keys(optimizedData.optimal_split || {}).map((provider) => (
                <View key={provider} style={styles.providerSection}>
                  <Text style={styles.providerName}>Buy on {provider}</Text>
                  {optimizedData.optimal_split[provider].map((item: any, i: number) => (
                    <View key={i} style={styles.itemRow}>
                      <Text style={styles.itemName} numberOfLines={1}>{item.product_name}</Text>
                      <Text style={styles.itemPrice}>₹{item.price}</Text>
                    </View>
                  ))}
                </View>
              ))}

              <View style={styles.totalsBox}>
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Items Total</Text>
                  <Text style={styles.totalValue}>₹{optimizedData.financials?.items_total}</Text>
                </View>
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Delivery Fees</Text>
                  <Text style={styles.totalValue}>₹{optimizedData.financials?.delivery_fees}</Text>
                </View>
                <View style={styles.grandTotalRow}>
                  <Text style={styles.grandTotalLabel}>Grand Total</Text>
                  <Text style={styles.grandTotalValue}>₹{optimizedData.financials?.grand_total}</Text>
                </View>
              </View>

              <TouchableOpacity style={[styles.checkoutBtn, { backgroundColor: color }]}>
                <Text style={styles.checkoutBtnText}>Auto-Checkout Split Carts 🚀</Text>
              </TouchableOpacity>

            </ScrollView>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>Add items to your cart first.</Text>
            </View>
          )}

        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    height: '80%',
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -10 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 10,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 22,
    fontWeight: '900',
    color: '#111827',
  },
  closeBtn: {
    padding: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  closeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4B5563',
  },
  loadingState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },
  scrollArea: {
    flex: 1,
  },
  recommendationBox: {
    backgroundColor: '#EEF2FF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#C7D2FE',
  },
  recommendationText: {
    color: '#4F46E5',
    fontWeight: '700',
    fontSize: 16,
    lineHeight: 24,
  },
  providerSection: {
    marginBottom: 24,
  },
  providerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    paddingBottom: 8,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  itemName: {
    fontSize: 15,
    color: '#4B5563',
    flex: 1,
    marginRight: 16,
  },
  itemPrice: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  totalsBox: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 16,
    marginBottom: 24,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  totalLabel: {
    color: '#6B7280',
    fontSize: 15,
  },
  totalValue: {
    color: '#374151',
    fontSize: 15,
    fontWeight: '500',
  },
  grandTotalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  grandTotalLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  grandTotalValue: {
    fontSize: 20,
    fontWeight: '900',
    color: '#10B981',
  },
  checkoutBtn: {
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 40,
  },
  checkoutBtnText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
  }
});
