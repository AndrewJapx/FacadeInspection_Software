"""
Chat Data Manager - Handle chat messages and photos for pins
Stores chat data separately from pins for better organization and tracking
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

class ChatDataManager:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'storage'))
        self.project_dir = os.path.join(self.storage_dir, project_name)
        self.chat_data_dir = os.path.join(self.project_dir, 'chat_data')
        self.photos_dir = os.path.join(self.chat_data_dir, 'photos')
        
        # Ensure directories exist
        os.makedirs(self.chat_data_dir, exist_ok=True)
        os.makedirs(self.photos_dir, exist_ok=True)
    
    def get_chat_file_path(self, pin_id: int) -> str:
        """Get the file path for a pin's chat data"""
        return os.path.join(self.chat_data_dir, f"pin_{pin_id}_chat.json")
    
    def load_pin_chat(self, pin_id: int) -> List[Dict[str, Any]]:
        """Load chat messages for a specific pin"""
        chat_file = self.get_chat_file_path(pin_id)
        if not os.path.exists(chat_file):
            return []
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load chat for pin {pin_id}: {e}")
            return []
    
    def save_pin_chat(self, pin_id: int, chat_messages: List[Dict[str, Any]]) -> bool:
        """Save chat messages for a specific pin"""
        chat_file = self.get_chat_file_path(pin_id)
        
        try:
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_messages, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] Saved chat data for pin {pin_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save chat for pin {pin_id}: {e}")
            return False
    
    def add_text_message(self, pin_id: int, message: str, author: str = "User") -> bool:
        """Add a text message to pin's chat"""
        chat_messages = self.load_pin_chat(pin_id)
        
        new_message = {
            "type": "text",
            "text": message,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        chat_messages.append(new_message)
        return self.save_pin_chat(pin_id, chat_messages)
    
    def add_photo_message(self, pin_id: int, photo_path: str, caption: str = "", author: str = "User") -> Optional[str]:
        """
        Add a photo to pin's chat and copy it to the project's photos directory
        Returns the new photo path or None if failed
        """
        if not os.path.exists(photo_path):
            print(f"[ERROR] Photo file does not exist: {photo_path}")
            return None
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(photo_path)[1].lower()
        new_filename = f"pin_{pin_id}_{timestamp}{file_ext}"
        new_photo_path = os.path.join(self.photos_dir, new_filename)
        
        try:
            # Copy photo to project directory
            shutil.copy2(photo_path, new_photo_path)
            print(f"[INFO] Copied photo to: {new_photo_path}")
            
            # Add to chat messages
            chat_messages = self.load_pin_chat(pin_id)
            
            new_message = {
                "type": "photo",
                "path": new_photo_path,
                "original_path": photo_path,
                "filename": new_filename,
                "caption": caption,
                "author": author,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            chat_messages.append(new_message)
            
            if self.save_pin_chat(pin_id, chat_messages):
                return new_photo_path
            else:
                # If saving chat failed, remove the copied photo
                if os.path.exists(new_photo_path):
                    os.remove(new_photo_path)
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to add photo for pin {pin_id}: {e}")
            return None
    
    def get_pin_photos(self, pin_id: int) -> List[Dict[str, Any]]:
        """Get all photos for a specific pin"""
        chat_messages = self.load_pin_chat(pin_id)
        return [msg for msg in chat_messages if msg.get('type') == 'photo']
    
    def get_pin_text_messages(self, pin_id: int) -> List[Dict[str, Any]]:
        """Get all text messages for a specific pin"""
        chat_messages = self.load_pin_chat(pin_id)
        return [msg for msg in chat_messages if msg.get('type') == 'text']
    
    def delete_pin_chat(self, pin_id: int) -> bool:
        """Delete all chat data for a pin (including photos)"""
        try:
            # Get photos to delete
            photos = self.get_pin_photos(pin_id)
            
            # Delete photo files
            for photo in photos:
                photo_path = photo.get('path')
                if photo_path and os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"[INFO] Deleted photo: {photo_path}")
            
            # Delete chat file
            chat_file = self.get_chat_file_path(pin_id)
            if os.path.exists(chat_file):
                os.remove(chat_file)
                print(f"[INFO] Deleted chat file: {chat_file}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete chat data for pin {pin_id}: {e}")
            return False
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get statistics about chat data for the project"""
        try:
            chat_files = [f for f in os.listdir(self.chat_data_dir) if f.endswith('_chat.json')]
            photo_files = [f for f in os.listdir(self.photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
            
            total_messages = 0
            total_photos = 0
            
            for chat_file in chat_files:
                try:
                    with open(os.path.join(self.chat_data_dir, chat_file), 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                        total_messages += len([m for m in messages if m.get('type') == 'text'])
                        total_photos += len([m for m in messages if m.get('type') == 'photo'])
                except:
                    continue
            
            return {
                "pins_with_chat": len(chat_files),
                "total_text_messages": total_messages,
                "total_photos": total_photos,
                "photo_files_on_disk": len(photo_files)
            }
        except Exception as e:
            print(f"[ERROR] Failed to get project stats: {e}")
            return {}

    def migrate_existing_chat_data(self, pins: List[Dict[str, Any]]) -> bool:
        """Migrate existing chat data from pins.json to separate chat files"""
        try:
            migrated_count = 0
            
            for pin in pins:
                pin_id = pin.get('pin_id')
                if not pin_id:
                    continue
                
                existing_chat = pin.get('chat', [])
                if not existing_chat:
                    continue
                
                # Convert old chat format to new format
                new_chat_messages = []
                for msg in existing_chat:
                    if isinstance(msg, str):
                        # Old format: just text strings
                        new_chat_messages.append({
                            "type": "text",
                            "text": msg,
                            "author": "User",
                            "timestamp": datetime.now().isoformat(),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "migrated": True
                        })
                    elif isinstance(msg, dict):
                        # Already in new format or partial format
                        if 'type' not in msg:
                            msg['type'] = 'text'
                        if 'timestamp' not in msg:
                            msg['timestamp'] = datetime.now().isoformat()
                        if 'author' not in msg:
                            msg['author'] = 'User'
                        new_chat_messages.append(msg)
                
                if new_chat_messages:
                    if self.save_pin_chat(pin_id, new_chat_messages):
                        migrated_count += 1
                        print(f"[INFO] Migrated chat data for pin {pin_id}")
            
            print(f"[INFO] Migration completed: {migrated_count} pins with chat data")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate chat data: {e}")
            return False