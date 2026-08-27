import { Fragment } from 'react'

/** As mensagens de aviso vêm de core/confianca.py com **negrito** em
 * Markdown (pensado originalmente pro st.error do Streamlit, que
 * renderiza Markdown nativamente). Em vez de reformatar essas strings
 * no backend só pra servir a um front-end específico, faz esse parse
 * mínimo aqui -- suporta só **negrito**, de propósito (nada além do
 * que essas mensagens realmente usam). */
export function TextoMarkdownLeve({ texto }: { texto: string }) {
  const partes = texto.split(/(\*\*[^*]+\*\*)/g)
  return (
    <>
      {partes.map((parte, i) => {
        if (parte.startsWith('**') && parte.endsWith('**')) {
          return <strong key={i}>{parte.slice(2, -2)}</strong>
        }
        return <Fragment key={i}>{parte}</Fragment>
      })}
    </>
  )
}
