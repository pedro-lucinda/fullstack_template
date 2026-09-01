import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { useTodoStore } from "@/store/todoStore";

export function TodosPage() {
  const { todos, isLoading, error, fetchTodos, addTodo, toggleTodo, removeTodo } = useTodoStore();
  const [title, setTitle] = useState("");

  useEffect(() => {
    void fetchTodos();
  }, [fetchTodos]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) return;
    await addTodo(trimmed);
    setTitle("");
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          aria-label="New todo title"
        />
        <Button type="submit" disabled={!title.trim()}>
          Add
        </Button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

      <div className="space-y-2">
        {todos.map((todo) => (
          <Card key={todo.id}>
            <CardContent className="flex items-center justify-between p-4">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggleTodo(todo.id)}
                  className="h-4 w-4"
                />
                <span className={todo.completed ? "text-muted-foreground line-through" : ""}>
                  {todo.title}
                </span>
              </label>
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete ${todo.title}`}
                onClick={() => removeTodo(todo.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
        {!isLoading && todos.length === 0 && (
          <p className="text-sm text-muted-foreground">No todos yet. Add one above.</p>
        )}
      </div>
    </div>
  );
}
