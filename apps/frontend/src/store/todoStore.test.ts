import { useTodoStore } from "@/store/todoStore";

jest.mock("@/api/generated/clients/createTodoApiV1TodosPost");
jest.mock("@/api/generated/clients/listTodosApiV1TodosGet");
jest.mock("@/api/generated/clients/toggleTodoApiV1TodosTodoIdTogglePatch");
jest.mock("@/api/generated/clients/deleteTodoApiV1TodosTodoIdDelete");

import { createTodoApiV1TodosPost } from "@/api/generated/clients/createTodoApiV1TodosPost";
import { listTodosApiV1TodosGet } from "@/api/generated/clients/listTodosApiV1TodosGet";
import { toggleTodoApiV1TodosTodoIdTogglePatch } from "@/api/generated/clients/toggleTodoApiV1TodosTodoIdTogglePatch";
import { deleteTodoApiV1TodosTodoIdDelete } from "@/api/generated/clients/deleteTodoApiV1TodosTodoIdDelete";

const mockedList = listTodosApiV1TodosGet as jest.Mock;
const mockedCreate = createTodoApiV1TodosPost as jest.Mock;
const mockedToggle = toggleTodoApiV1TodosTodoIdTogglePatch as jest.Mock;
const mockedDelete = deleteTodoApiV1TodosTodoIdDelete as jest.Mock;

const sampleTodo = {
  id: "1",
  title: "Buy milk",
  completed: false,
  created_at: "2024-01-01T00:00:00Z",
};

beforeEach(() => {
  jest.clearAllMocks();
  useTodoStore.setState({ todos: [], isLoading: false, error: null });
});

describe("useTodoStore", () => {
  it("fetchTodos populates todos on success", async () => {
    mockedList.mockResolvedValue([sampleTodo]);

    await useTodoStore.getState().fetchTodos();

    expect(useTodoStore.getState().todos).toEqual([sampleTodo]);
    expect(useTodoStore.getState().isLoading).toBe(false);
    expect(useTodoStore.getState().error).toBeNull();
  });

  it("fetchTodos sets error on failure", async () => {
    mockedList.mockRejectedValue(new Error("network down"));

    await useTodoStore.getState().fetchTodos();

    expect(useTodoStore.getState().error).toBe("network down");
    expect(useTodoStore.getState().todos).toEqual([]);
  });

  it("addTodo prepends the new todo", async () => {
    mockedCreate.mockResolvedValue(sampleTodo);

    await useTodoStore.getState().addTodo("Buy milk");

    expect(useTodoStore.getState().todos).toEqual([sampleTodo]);
  });

  it("toggleTodo replaces the updated todo", async () => {
    useTodoStore.setState({ todos: [sampleTodo] });
    const toggled = { ...sampleTodo, completed: true };
    mockedToggle.mockResolvedValue(toggled);

    await useTodoStore.getState().toggleTodo("1");

    expect(useTodoStore.getState().todos).toEqual([toggled]);
  });

  it("removeTodo removes the todo from state", async () => {
    useTodoStore.setState({ todos: [sampleTodo] });
    mockedDelete.mockResolvedValue(undefined);

    await useTodoStore.getState().removeTodo("1");

    expect(useTodoStore.getState().todos).toEqual([]);
  });
});
