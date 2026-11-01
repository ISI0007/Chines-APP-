import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, Pressable, ScrollView, Text, View } from "react-native";
import { FlashcardAPI, ReaderAPI, MockTestAPI, ProgressAPI, type Book, type BookDetail } from "../services/api";
import { Failure, ui } from "../components/StudyUI";

export default function Phase2ReaderScreen() {
  const [books, setBooks] = useState<Book[]>([]), [book, setBook] = useState<BookDetail | null>(null);
  const [busy, setBusy] = useState(true), [error, setError] = useState(""), [pinyin, setPinyin] = useState(true), [retry, setRetry] = useState(0);
  useEffect(() => { const controller = new AbortController(); setBusy(true); setError(""); ReaderAPI.books(controller.signal).then(data => { if (!controller.signal.aborted) setBooks(data); }).catch(() => { if (!controller.signal.aborted) setError("Could not load books."); }).finally(() => { if (!controller.signal.aborted) setBusy(false); }); return () => controller.abort(); }, [retry]);
  async function open(id: number) { setBusy(true); setError(""); try { setBook(await ReaderAPI.book(id)); } catch { setError("Could not load this book."); } finally { setBusy(false); } }
  return <ScrollView contentContainerStyle={ui.page}><Text style={ui.title}>Graded readers</Text>
    {book && <Button title="Back to books" onPress={() => setBook(null)} />}
    {busy ? <ActivityIndicator /> : error ? <Failure message={error} retry={() => { setError(""); if (book) void open(book.id); else setRetry(n => n + 1); }} /> : book ? <>
      <Text style={ui.pinyin}>{book.title}</Text><Button title={pinyin ? "Hide pinyin" : "Show pinyin"} onPress={() => setPinyin(!pinyin)} />
      {book.pages.map(page => <View key={page.id} style={ui.card}><Text selectable style={{ fontSize: 25, lineHeight: 40 }}>{page.content}</Text>{pinyin && !!page.pinyin && <Text selectable style={ui.pinyin}>{page.pinyin}</Text>}{page.definitions && Object.entries(page.definitions).map(([character, meaning]) => <Text key={character}>{character} · {meaning}</Text>)}</View>)}
    </> : books.length ? books.map(item => <Pressable key={item.id} accessibilityRole="button" onPress={() => void open(item.id)} style={ui.card}><Text style={ui.pinyin}>{item.title}</Text><Text>{item.hsk_level}</Text>{!!item.description && <Text>{item.description}</Text>}</Pressable>) : <Text>No books available yet.</Text>}
  </ScrollView>;
}

