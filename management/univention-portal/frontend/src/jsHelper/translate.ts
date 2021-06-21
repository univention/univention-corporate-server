import { catalog } from '@/assets/data/dictionary';

export default function translateLabel(translationLabel: string): string {
  return catalog[translationLabel].translated.value;
}
