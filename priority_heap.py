"""
priority_heap.py - Sistema de gestión de prioridades
Implementa un heap de prioridad para gestionar tareas y acciones
"""

import heapq
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
    Heap de prioridad para gestionar tareas
    Prioridad más baja = más importante (se procesa primero)
    """
    
    def __init__(self):
        self._heap: List[PriorityItem] = []
        self._counter: int = 0
        self._entry_finder: dict = {}
        self._REMOVED = '<removed-task>'
    
    def push(self, item: Any, priority: int = 0):
        """
        Agrega un elemento al heap con su prioridad
        Prioridad más baja se procesa primero
        """
        if item in self._entry_finder:
            self.remove(item)
        
        self._counter += 1
        entry = PriorityItem(priority=priority, item=item, counter=self._counter)
        self._entry_finder[item] = entry
        heapq.heappush(self._heap, entry)
    
    def pop(self) -> Optional[Any]:
        """
        Extrae y retorna el elemento de mayor prioridad (menor valor)
        Retorna None si el heap está vacío
        """
        while self._heap:
            entry = heapq.heappop(self._heap)
            if entry.item is not self._REMOVED:
                del self._entry_finder[entry.item]
                return entry.item
        return None
    
    def peek(self) -> Optional[Any]:
        """
        Retorna el elemento de mayor prioridad sin extraerlo
        Retorna None si el heap está vacío
        """
        while self._heap:
            entry = self._heap[0]
            if entry.item is not self._REMOVED:
                return entry.item
            heapq.heappop(self._heap)
        return None
    
    def remove(self, item: Any) -> bool:
        """
        Marca un elemento como removido
        El elemento se eliminará cuando llegue su turno
        """
        if item not in self._entry_finder:
            return False
        
        entry = self._entry_finder.pop(item)
        entry.item = self._REMOVED
        return True
    
    def update_priority(self, item: Any, new_priority: int):
        """
        Actualiza la prioridad de un elemento
        Si el elemento no existe, lo agrega
        """
        self.remove(item)
        self.push(item, new_priority)
    
    def contains(self, item: Any) -> bool:
        """Verifica si un elemento está en el heap"""
        return item in self._entry_finder
    
    def get_priority(self, item: Any) -> Optional[int]:
        """Obtiene la prioridad de un elemento"""
        if item not in self._entry_finder:
            return None
        return self._entry_finder[item].priority
    
    def is_empty(self) -> bool:
        """Verifica si el heap está vacío"""
        return len(self._entry_finder) == 0
    
    def size(self) -> int:
        """Retorna el número de elementos en el heap"""
        return len(self._entry_finder)
    
    def clear(self):
        """Limpia todos los elementos del heap"""
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
        """
        Retorna los n elementos de mayor prioridad sin extraerlos
        """
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


# Ejemplo de uso
if __name__ == "__main__":
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
