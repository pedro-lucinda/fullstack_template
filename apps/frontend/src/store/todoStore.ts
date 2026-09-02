import { create } from "zustand";

import { createTodoApiV1TodosPost } from "@/api/generated/clients/createTodoApiV1TodosPost";
import { listTodosApiV1TodosGet } from "@/api/generated/clients/listTodosApiV1TodosGet";
import { toggleTodoApiV1TodosTodoIdTogglePatch } from "@/api/generated/clients/toggleTodoApiV1TodosTodoIdTogglePatch";
import { deleteTodoApiV1TodosTodoIdDelete } from "@/api/generated/clients/deleteTodoApiV1TodosTodoIdDelete";
import type { TodoRead } from "@/api/generated/types/TodoRead";

interface TodoState {
  todos: TodoRead[];
  isLoading: boolean;
  error: string | null;
  fetchTodos: () => Promise<void>;
  addTodo: (title: string) => Promise<void>;
  toggleTodo: (id: string) => Promise<void>;
  removeTodo: (id: string) => Promise<void>;
}

/** Zustand store for the Todos feature. Talks to the backend exclusively via
 * the Kubb-generated typed client (see specs/todos/design.md). */
export const useTodoStore = create<TodoState>((set, get) => ({
  todos: [],
  isLoading: false,
  error: null,

  fetchTodos: async () => {
    set({ isLoading: true, error: null });
    try {
      const { items } = await listTodosApiV1TodosGet();
      set({ todos: items, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  addTodo: async (title: string) => {
    set({ error: null });
    try {
      const todo = await createTodoApiV1TodosPost({ title });
      set({ todos: [todo, ...get().todos] });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  toggleTodo: async (id: string) => {
    set({ error: null });
    try {
      const updated = await toggleTodoApiV1TodosTodoIdTogglePatch(id);
      set({ todos: get().todos.map((t) => (t.id === id ? updated : t)) });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  removeTodo: async (id: string) => {
    set({ error: null });
    try {
      await deleteTodoApiV1TodosTodoIdDelete(id);
      set({ todos: get().todos.filter((t) => t.id !== id) });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },
}));
