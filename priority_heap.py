"""
priority_heap.py - Sistema de gestión de prioridades
🔥 IMPLEMENTACIÓN 100% PROPIA - SIN HEAPQ
Implementa un Min-Heap completamente desde cero
"""

from typing import Any, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass(order=True)
class PriorityItem:
    """Elemento con prioridad para el heap"""
    priority: int
    item: Any = field(compare=False)
    counter: int = field(default=0, compare=True)
    
    def __repr__(self) -> str:
        return f"PriorityItem(priority={self.priority}, item={self.item})"


class PriorityHeap:
    """
    🧠 HEAP DE PRIORIDAD PROPIO - Sin librerías externas
    Implementación completa de Min-Heap desde cero
    
    Algoritmos propios:
    - Heapify Up (Bubble Up) - O(log n)
    - Heapify Down (Bubble Down) - O(log n)
    - Inserción - O(log n)
    - Extracción - O(log n)
    
    Prioridad más baja = más importante (se procesa primero)
    """
    
    def __init__(self):
        self._heap: List[PriorityItem] = []
        self._counter: int = 0
        self._entry_finder: dict = {}
        self._REMOVED = '<removed-task>'
    
    # ========== ALGORITMOS PROPIOS DEL HEAP ==========
    
    def _parent_index(self, index: int) -> int:
        """Índice del padre: (i-1)//2"""
        return (index - 1) // 2
    
    def _left_child_index(self, index: int) -> int:
        """Índice del hijo izquierdo: 2*i + 1"""
        return 2 * index + 1
    
    def _right_child_index(self, index: int) -> int:
        """Índice del hijo derecho: 2*i + 2"""
        return 2 * index + 2
    
    def _has_parent(self, index: int) -> bool:
        """¿Tiene padre?"""
        return self._parent_index(index) >= 0
    
    def _has_left_child(self, index: int) -> bool:
        """¿Tiene hijo izquierdo?"""
        return self._left_child_index(index) < len(self._heap)
    
    def _has_right_child(self, index: int) -> bool:
        """¿Tiene hijo derecho?"""
        return self._right_child_index(index) < len(self._heap)
    
    def _parent(self, index: int) -> PriorityItem:
        """Obtener elemento padre"""
        return self._heap[self._parent_index(index)]
    
    def _left_child(self, index: int) -> PriorityItem:
        """Obtener hijo izquierdo"""
        return self._heap[self._left_child_index(index)]
    
    def _right_child(self, index: int) -> PriorityItem:
        """Obtener hijo derecho"""
        return self._heap[self._right_child_index(index)]
    
    def _swap(self, index1: int, index2: int):
        """🔄 Intercambiar dos elementos"""
        self._heap[index1], self._heap[index2] = self._heap[index2], self._heap[index1]
    
    def _heapify_up(self, index: int):
        """
        ⬆️ ALGORITMO PROPIO: HEAPIFY UP (Bubble Up)
        Mueve elemento hacia arriba hasta mantener propiedad min-heap
        """
        while self._has_parent(index) and self._parent(index) > self._heap[index]:
            parent_idx = self._parent_index(index)
            self._swap(index, parent_idx)
            index = parent_idx
    
    def _heapify_down(self, index: int):
        """
        ⬇️ ALGORITMO PROPIO: HEAPIFY DOWN (Bubble Down)
        Mueve elemento hacia abajo hasta mantener propiedad min-heap
        """
        while self._has_left_child(index):
            smaller_child_index = self._left_child_index(index)
            
            if (self._has_right_child(index) and 
                self._right_child(index) < self._left_child(index)):
                smaller_child_index = self._right_child_index(index)
            
            if self._heap[index] <= self._heap[smaller_child_index]:
                break
            
            self._swap(index, smaller_child_index)
            index = smaller_child_index
    
    def _extract_root(self):
        """🗑️ ALGORITMO PROPIO: Extraer raíz y reorganizar"""
        if not self._heap:
            return
        
        if len(self._heap) == 1:
            self._heap.pop()
            return
        
        # Mover último elemento a la raíz
        self._heap[0] = self._heap.pop()
        # Heapify down desde la raíz
        self._heapify_down(0)
    
    # ========== OPERACIONES PÚBLICAS ==========
    
    def push(self, item: Any, priority: int = 0):
        """
        ➕ INSERCIÓN PROPIA
        Agrega elemento al heap con su prioridad
        Prioridad más baja se procesa primero
        """
        if item in self._entry_finder:
            self.remove(item)
        
        self._counter += 1
        entry = PriorityItem(priority=priority, item=item, counter=self._counter)
        
        # Agregar al final
        self._heap.append(entry)
        self._entry_finder[item] = entry
        
        # 🔥 Heapify up propio
        self._heapify_up(len(self._heap) - 1)
    
    def pop(self) -> Optional[Any]:
        """
        ⬆️ EXTRACCIÓN PROPIA
        Extrae y retorna elemento de mayor prioridad (menor valor)
        Retorna None si el heap está vacío
        """
        # Limpiar elementos removidos
        while self._heap and self._heap[0].item is self._REMOVED:
            self._extract_root()
        
        if not self._heap:
            return None
        
        # Guardar el mínimo
        min_item = self._heap[0]
        
        if min_item.item in self._entry_finder:
            del self._entry_finder[min_item.item]
        
        # 🔥 Extraer raíz con algoritmo propio
        self._extract_root()
        
        return min_item.item
    
    def peek(self) -> Optional[Any]:
        """
        👁️ VER MÍNIMO
        Retorna elemento de mayor prioridad sin extraerlo
        """
        while self._heap and self._heap[0].item is self._REMOVED:
            self._extract_root()
        
        if self._heap:
            return self._heap[0].item
        return None
    
    def remove(self, item: Any) -> bool:
        """
        🗑️ ELIMINACIÓN PROPIA
        Marca elemento como removido (eliminación perezosa)
        """
        if item not in self._entry_finder:
            return False
        
        entry = self._entry_finder.pop(item)
        entry.item = self._REMOVED
        
        # Si está en la raíz, limpiar inmediatamente
        if self._heap and self._heap[0].item is self._REMOVED:
            self._extract_root()
        
        return True
    
    def update_priority(self, item: Any, new_priority: int):
        """
        🔄 ACTUALIZACIÓN DE PRIORIDAD
        Actualiza prioridad de un elemento
        """
        self.remove(item)
        self.push(item, new_priority)
    
    def contains(self, item: Any) -> bool:
        """Verifica si elemento está en el heap"""
        return item in self._entry_finder
    
    def get_priority(self, item: Any) -> Optional[int]:
        """Obtiene prioridad de un elemento"""
        if item not in self._entry_finder:
            return None
        return self._entry_finder[item].priority
    
    def is_empty(self) -> bool:
        """Verifica si el heap está vacío"""
        return len(self._entry_finder) == 0
    
    def size(self) -> int:
        """Retorna número de elementos"""
        return len(self._entry_finder)
    
    def clear(self):
        """Limpia todos los elementos"""
        self._heap.clear()
        self._entry_finder.clear()
        self._counter = 0
    
    def get_all_items(self) -> List[Tuple[Any, int]]:
        """
        Retorna todos los elementos con sus prioridades
        Como lista de tuplas (item, priority)
        """
        items = []
        for item, entry in self._entry_finder.items():
            if entry.item is not self._REMOVED:
                items.append((item, entry.priority))
        
        # Ordenar por prioridad (menor primero)
        items.sort(key=lambda x: x[1])
        return items
    
    def get_top_n(self, n: int) -> List[Any]:
        """Retorna los n elementos de mayor prioridad"""
        all_items = self.get_all_items()
        return [item for item, _ in all_items[:n]]
    
    def __len__(self) -> int:
        return self.size()
    
    def __bool__(self) -> bool:
        return not self.is_empty()
    
    def __contains__(self, item: Any) -> bool:
        return self.contains(item)
    
    def __repr__(self) -> str:
        items = self.get_all_items()
        items_str = ", ".join([f"{item}({priority})" for item, priority in items[:5]])
        if len(items) > 5:
            items_str += f"... (+{len(items) - 5} más)"
        return f"PriorityHeap([{items_str}])"


# 🧪 Ejemplo de uso y pruebas
if __name__ == "__main__":
    print("🔥 PRIORITY HEAP - 100% PROPIO (SIN HEAPQ)")
    print("=" * 50)
    
    heap = PriorityHeap()
    
    # Agregar tareas con diferentes prioridades
    heap.push("Tarea urgente", priority=1)
    heap.push("Tarea normal", priority=5)
    heap.push("Tarea baja prioridad", priority=10)
    heap.push("Tarea muy urgente", priority=0)
    
    print("Heap:", heap)
    print(f"Tamaño: {len(heap)}")
    
    # Ver el siguiente sin extraer
    print(f"\nSiguiente tarea: {heap.peek()}")
    
    # Extraer tareas en orden de prioridad
    print("\nExtrayendo tareas:")
    while not heap.is_empty():
        tarea = heap.pop()
        print(f"  - {tarea}")
    
    print(f"\n¿Heap vacío? {heap.is_empty()}")
    print("\n✅ ¡Heap 100% propio sin heapq!")
