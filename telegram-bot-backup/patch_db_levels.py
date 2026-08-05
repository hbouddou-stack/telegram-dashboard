import sqlite3

def patch_db():
    conn = sqlite3.connect('backup_bot.db')
    cursor = conn.cursor()
    
    try:
        # Step 1: Shift all levels down by 1 (where level > 1)
        cursor.execute("UPDATE thematic_nodes SET level = level - 1 WHERE level > 1")
        print(f"Shifted levels down for {cursor.rowcount} nodes.")
        
        # Step 2: Get current Fiqh root nodes (now level 1, parent_id is null)
        cursor.execute("SELECT id, title FROM thematic_nodes WHERE program_id = 1 AND parent_id IS NULL")
        fiqh_roots = cursor.fetchall()
        print(f"Found {len(fiqh_roots)} Fiqh root nodes.")
        
        # Step 3: Insert new Fiqh Level 1 nodes
        new_fiqh_nodes = [
            ("الطهارة", 1, 1),
            ("الصلاة", 1, 2),
            ("الصيام", 1, 3),
            ("الزكاة", 1, 4),
            ("الحج", 1, 5)
        ]
        
        prayer_node_id = None
        for title, level, order_index in new_fiqh_nodes:
            cursor.execute('''
                INSERT INTO thematic_nodes (program_id, parent_id, level, title, order_index, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (1, None, level, title, order_index, 1))
            new_id = cursor.lastrowid
            if title == "الصلاة":
                prayer_node_id = new_id
                
        print(f"Created new Fiqh root nodes. Prayer node ID is {prayer_node_id}")
        
        # Step 4: Reparent existing Fiqh root nodes to the new 'الصلاة' node
        # Also need to increase their level back to 2, and their children to 3, etc.
        # Wait, if they were level 2, we just shifted them to level 1.
        # If we reparent them, they should be level 2 again, their children level 3, etc.
        # Let's get all descendants of these old Fiqh roots and shift them UP by 1.
        
        old_root_ids = [r[0] for r in fiqh_roots]
        
        # We need a recursive function to shift levels up by 1 for a subtree
        def shift_subtree_up(node_id):
            cursor.execute("UPDATE thematic_nodes SET level = level + 1 WHERE id = ?", (node_id,))
            cursor.execute("SELECT id FROM thematic_nodes WHERE parent_id = ?", (node_id,))
            children = cursor.fetchall()
            for child in children:
                shift_subtree_up(child[0])
                
        if prayer_node_id:
            for old_root_id in old_root_ids:
                # Update parent
                cursor.execute("UPDATE thematic_nodes SET parent_id = ? WHERE id = ?", (prayer_node_id, old_root_id))
                # Shift levels back up for this node and its descendants
                shift_subtree_up(old_root_id)
                
        print("Reparented existing Fiqh prayer nodes.")
        
        conn.commit()
        print("DB migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_db()
