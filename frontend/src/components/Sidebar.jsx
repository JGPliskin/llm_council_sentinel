import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { Trash2, X, CheckSquare, Square } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onBulkDeleteConversations,
}) {
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  // Confirmation State
  const [confirmState, setConfirmState] = useState({ open: false, type: "single", id: null });

  // Sync selectedIds with conversations (cleanup deleted IDs)
  useEffect(() => {
    if (selectedIds.size > 0) {
      const validIds = new Set();
      conversations.forEach(c => {
        if (selectedIds.has(c.id)) validIds.add(c.id);
      });
      if (validIds.size !== selectedIds.size) {
        setSelectedIds(validIds);
      }
    }
  }, [conversations, selectedIds]);

  const handleToggleSelectMode = () => {
    setIsSelectMode(!isSelectMode);
    setSelectedIds(new Set());
  };

  const handleToggleSelect = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedIds.size === conversations.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(conversations.map((c) => c.id)));
    }
  };

  const handleDeleteSingle = async (id) => {
    setConfirmState({ open: false, type: "single", id: null });
    setIsDeleting(true);
    try {
      if (onDeleteConversation) {
        await onDeleteConversation(id);
      }
    } catch (error) {
      console.error("Delete failed", error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteBulk = async () => {
    setConfirmState({ open: false, type: "bulk", id: null });
    if (selectedIds.size === 0) return;

    setIsDeleting(true);
    try {
      if (onBulkDeleteConversations) {
        const ids = Array.from(selectedIds);
        const result = await onBulkDeleteConversations(ids);

        // Handle result logic
        if (result) {
          const { failed } = result;
          if (failed && failed.length > 0) {
            // Partial failure: keep failed IDs selected
            const failedSet = new Set(failed.map(f => f.id));
            setSelectedIds(failedSet);
            toast.error(`Failed to delete ${failed.length} conversations`);
          } else {
            // All success
            setIsSelectMode(false);
            setSelectedIds(new Set());
            toast.success("Conversations deleted");
          }
        }
      }
    } catch (error) {
      console.error("Bulk delete failed", error);
    } finally {
      setIsDeleting(false);
    }
  };

  const initiateSingleDelete = (e, id) => {
    e.stopPropagation();
    setConfirmState({ open: true, type: "single", id });
  };

  return (
    <div className="flex h-full w-full flex-col border-r bg-card overflow-hidden">
      <div className="border-b p-4 flex-shrink-0">
        <h1 className="mb-4 text-xl font-bold text-foreground truncate">
          LLM Council
        </h1>

        {!isSelectMode ? (
          <div className="flex flex-col gap-2">
            <Button onClick={onNewConversation} className="w-full" disabled={isDeleting}>
              + New Conversation
            </Button>
            {conversations.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleToggleSelectMode}
                className="w-full text-muted-foreground h-8"
                disabled={isDeleting}
              >
                Select Conversations
              </Button>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-1">
              <Button variant="ghost" size="sm" onClick={() => setIsSelectMode(false)} disabled={isDeleting}>
                Cancel
              </Button>
              <Button variant="ghost" size="sm" onClick={handleSelectAll} disabled={isDeleting}>
                {selectedIds.size === conversations.length ? "Unselect All" : "Select All"}
              </Button>
            </div>
            <Button
              variant="destructive"
              size="sm"
              className="w-full"
              disabled={selectedIds.size === 0 || isDeleting}
              onClick={() => setConfirmState({ open: true, type: "bulk" })}
            >
              Delete Selected ({selectedIds.size})
            </Button>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1 min-h-0" scrollHideDelay={0}>
        <div className="p-3 pr-4 overflow-hidden">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  "group flex items-start justify-between gap-2 mb-2 rounded-lg p-3 transition-all hover:bg-muted/50 hover:shadow-sm overflow-hidden",
                  // Only show active state if NOT in select mode
                  !isSelectMode && conv.id === currentConversationId && "bg-primary/10 border border-primary shadow-sm",
                  isSelectMode ? "cursor-default" : "cursor-pointer"
                )}
                onClick={(e) => {
                  if (isSelectMode) {
                    handleToggleSelect(conv.id);
                  } else {
                    onSelectConversation(conv.id);
                  }
                }}
              >
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  {isSelectMode && (
                    <Checkbox
                      checked={selectedIds.has(conv.id)}
                      onCheckedChange={() => handleToggleSelect(conv.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="mt-1"
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className={cn("mb-1 text-sm font-semibold truncate", isSelectMode && "text-foreground")}>
                      {conv.title || "New Conversation"}
                    </p>
                    <div className="text-xs text-muted-foreground mono">
                      {conv.message_count} messages
                    </div>
                  </div>
                </div>

                {!isSelectMode && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => initiateSingleDelete(e, conv.id)}
                    disabled={isDeleting}
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                  </Button>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      <AlertDialog open={confirmState.open} onOpenChange={(open) => !isDeleting && setConfirmState(prev => ({ ...prev, open }))}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirmState.type === "single" ? "Delete conversation?" : `Delete ${selectedIds.size} conversations?`}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmState.type === "single"
                ? "This will permanently delete this conversation and its messages."
                : "This will permanently delete the selected conversations and their messages."
              }
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault(); // Prevent auto-close
                if (confirmState.type === "single") handleDeleteSingle(confirmState.id);
                else handleDeleteBulk();
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
