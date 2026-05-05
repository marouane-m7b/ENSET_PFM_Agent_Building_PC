"""
Inventory Management System
Handles stock updates when builds are approved
"""
import pandas as pd
from typing import Dict, Any
import os

class InventoryManager:
    """Manages component inventory across CSV files"""
    
    COMPONENT_FILES = {
        'CPU': 'data/cpus.csv',
        'GPU': 'data/gpus.csv',
        'Motherboard': 'data/motherboards.csv',
        'RAM': 'data/ram.csv',
        'Storage': 'data/storage.csv',
        'Cooler': 'data/coolers.csv',
        'PSU': 'data/psus.csv',
        'Case': 'data/cases.csv'
    }
    
    @staticmethod
    def decrease_stock(components: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Decrease stock for each component in the build by 1.
        
        Args:
            components: Dictionary of components from the build
            
        Returns:
            Dictionary with success status for each component
        """
        results = {}
        
        for category, component in components.items():
            file_path = InventoryManager.COMPONENT_FILES.get(category)
            
            if not file_path or not os.path.exists(file_path):
                print(f"⚠️ File not found for {category}: {file_path}")
                results[category] = False
                continue
            
            try:
                # Read CSV
                df = pd.read_csv(file_path)
                
                # Find the component by Brand and Model
                brand = component.get('Brand', '')
                model = component.get('Model', '')
                
                # Find matching row
                mask = (df['Brand'] == brand) & (df['Model'] == model)
                matching_rows = df[mask]
                
                if len(matching_rows) == 0:
                    print(f"⚠️ Component not found: {brand} {model}")
                    results[category] = False
                    continue
                
                # Get current stock
                current_stock = df.loc[mask, 'Stock'].values[0]
                
                if current_stock <= 0:
                    print(f"⚠️ {category} already out of stock: {brand} {model}")
                    results[category] = False
                    continue
                
                # Decrease stock by 1
                df.loc[mask, 'Stock'] = current_stock - 1
                new_stock = current_stock - 1
                
                # Update Availability if stock reaches 0
                if new_stock == 0:
                    df.loc[mask, 'Availability'] = 'Out of Stock'
                    print(f"🔴 {category} now OUT OF STOCK: {brand} {model}")
                elif new_stock < 10:
                    print(f"⚠️ {category} LIMITED STOCK ({new_stock}): {brand} {model}")
                else:
                    print(f"✅ {category} stock updated ({new_stock}): {brand} {model}")
                
                # Save back to CSV
                df.to_csv(file_path, index=False)
                results[category] = True
                
            except Exception as e:
                print(f"❌ Error updating {category}: {e}")
                results[category] = False
        
        # Summary
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        print(f"\n📊 Inventory Update: {success_count}/{total_count} components updated")
        
        return results
    
    @staticmethod
    def get_stock_status(category: str, brand: str, model: str) -> Dict[str, Any]:
        """
        Get current stock status for a specific component.
        
        Args:
            category: Component category (CPU, GPU, etc.)
            brand: Component brand
            model: Component model
            
        Returns:
            Dictionary with stock information
        """
        file_path = InventoryManager.COMPONENT_FILES.get(category)
        
        if not file_path or not os.path.exists(file_path):
            return {'error': 'File not found', 'stock': 0}
        
        try:
            df = pd.read_csv(file_path)
            mask = (df['Brand'] == brand) & (df['Model'] == model)
            matching_rows = df[mask]
            
            if len(matching_rows) == 0:
                return {'error': 'Component not found', 'stock': 0}
            
            stock = int(matching_rows['Stock'].values[0])
            availability = matching_rows['Availability'].values[0]
            
            status = 'Out of Stock' if stock == 0 else ('Limited Stock' if stock < 10 else 'In Stock')
            
            return {
                'stock': stock,
                'availability': availability,
                'status': status
            }
            
        except Exception as e:
            return {'error': str(e), 'stock': 0}

# Global instance
inventory_manager = InventoryManager()
