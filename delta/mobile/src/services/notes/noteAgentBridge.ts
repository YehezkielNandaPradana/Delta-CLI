import { useNotesStore } from '../../store/useNotesStore';
import { Note } from '../../types/notes';

export interface AgentToolResult {
  success: boolean;
  message: string;
  data?: any;
}

export const noteAgentBridge = {
  /**
   * Create a new note from Agent directive
   */
  async createNote(params: {
    title: string;
    content: string;
    folderId?: string | null;
    folderName?: string;
    tags?: string[];
  }): Promise<AgentToolResult> {
    const { folders, createNote, createFolder } = useNotesStore.getState();

    let targetFolderId = params.folderId || null;
    if (!targetFolderId && params.folderName) {
      const existing = folders.find(
        (f) => f.name.toLowerCase() === params.folderName!.toLowerCase()
      );
      if (existing) {
        targetFolderId = existing.id;
      } else {
        const created = await createFolder(params.folderName);
        targetFolderId = created.id;
      }
    }

    const note = await createNote({
      title: params.title || 'Note',
      content: params.content || '',
      folderId: targetFolderId,
      tags: params.tags || [],
    });

    return {
      success: true,
      message: `Note created successfully: "${note.title}" (ID: ${note.id})`,
      data: note,
    };
  },

  /**
   * Search notes by keyword
   */
  async searchNotes(params: { query: string }): Promise<AgentToolResult> {
    const { notes } = useNotesStore.getState();
    const q = (params.query || '').toLowerCase().trim();

    const matches = notes.filter(
      (n) =>
        n.title.toLowerCase().includes(q) ||
        n.content.toLowerCase().includes(q) ||
        (n.tags && n.tags.some((t) => t.toLowerCase().includes(q)))
    );

    return {
      success: true,
      message: `Found ${matches.length} matching note(s)`,
      data: matches.map((m) => ({
        id: m.id,
        title: m.title,
        snippet: m.content.slice(0, 150),
        folderId: m.folderId,
        updatedAt: m.updatedAt,
      })),
    };
  },

  /**
   * Read full note content by ID or title
   */
  async readNote(params: { id?: string; title?: string }): Promise<AgentToolResult> {
    const { notes } = useNotesStore.getState();
    const note = notes.find(
      (n) =>
        (params.id && n.id === params.id) ||
        (params.title && n.title.toLowerCase() === params.title.toLowerCase())
    );

    if (!note) {
      return {
        success: false,
        message: `Note not found with query: ${JSON.stringify(params)}`,
      };
    }

    return {
      success: true,
      message: `Note retrieved: "${note.title}"`,
      data: note,
    };
  },

  /**
   * Update existing note content or title
   */
  async updateNote(params: {
    id: string;
    title?: string;
    content?: string;
    appendContent?: string;
  }): Promise<AgentToolResult> {
    const { notes, updateNote } = useNotesStore.getState();
    const existing = notes.find((n) => n.id === params.id);

    if (!existing) {
      return {
        success: false,
        message: `Note not found for update: ID ${params.id}`,
      };
    }

    let finalContent = params.content !== undefined ? params.content : existing.content;
    if (params.appendContent) {
      finalContent = `${finalContent}\n\n${params.appendContent}`;
    }

    await updateNote(params.id, {
      title: params.title !== undefined ? params.title : existing.title,
      content: finalContent,
    });

    return {
      success: true,
      message: `Note "${existing.title}" updated successfully`,
      data: { id: params.id },
    };
  },

  /**
   * Delete a note by ID
   */
  async deleteNote(params: { id: string }): Promise<AgentToolResult> {
    const { notes, deleteNote } = useNotesStore.getState();
    const existing = notes.find((n) => n.id === params.id);

    if (!existing) {
      return {
        success: false,
        message: `Note not found for deletion: ID ${params.id}`,
      };
    }

    await deleteNote(params.id);
    return {
      success: true,
      message: `Note "${existing.title}" deleted successfully`,
    };
  },

  /**
   * List all notes or notes inside a folder
   */
  async listNotes(params?: { folderId?: string }): Promise<AgentToolResult> {
    const { notes, folders } = useNotesStore.getState();

    let targetNotes = notes;
    if (params?.folderId) {
      targetNotes = notes.filter((n) => n.folderId === params.folderId);
    }

    return {
      success: true,
      message: `Listed ${targetNotes.length} note(s)`,
      data: targetNotes.map((n) => ({
        id: n.id,
        title: n.title,
        folderId: n.folderId,
        folderName: folders.find((f) => f.id === n.folderId)?.name || 'Unassigned',
        updatedAt: n.updatedAt,
      })),
    };
  },
};
