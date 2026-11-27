# Modelos UML — BarberFlow

Visões conceituais derivadas da spec; não afirmam que a implementação Python usa classes ORM. As entidades são persistidas em SQLite, e os serviços de aplicação são funções em módulos.

## Diagrama de classes do domínio

```mermaid
classDiagram
class Usuario {
  +id: int
  +nome: str
  +email: str
  +papel: enum
  +ativo: bool
}
class Barbeiro {
  +id: int
  +comissaoBps: int
}
class Expediente {
  +diaSemana: int
  +inicio: time
  +fim: time
}
class Servico {
  +id: int
  +nome: str
  +precoCentavos: int
  +duracaoMin: int
  +elegivel: bool
}
class Atendimento {
  +id: int
  +inicio: datetime
  +fim: datetime
  +estado: enum
  +precoSnapshot: int
  +comissaoSnapshot: int
  +valorPago: int
}
class Fila {
  +inicioJanela: datetime
  +fimJanela: datetime
  +estado: enum
}
class Oferta {
  +inicio: datetime
  +fim: datetime
  +expiraEm: datetime
  +estado: enum
}
class Recompensa {
  +estado: enum
}
class Credito {
  +criadoEm: datetime
}
class Insumo {
  +nome: str
  +quantidade: int
  +minimo: int
}
class Consumo {
  +quantidade: int
}
class Movimento {
  +delta: int
  +motivo: str
}
class Receita {
  +valorCentavos: int
}
class Comissao {
  +valorCentavos: int
}
class Despesa {
  +valorCentavos: int
  +descricao: str
}
class Avaliacao {
  +nota: int
  +comentario: str
}
class Notificacao {
  +mensagem: str
}
Usuario "1" -- "0..1" Barbeiro : perfil profissional
Barbeiro "1" *-- "0..*" Expediente
Usuario "1" -- "0..*" Atendimento : cliente
Barbeiro "1" -- "0..*" Atendimento
Servico "1" -- "0..*" Atendimento
Usuario "1" -- "0..*" Fila : cliente
Barbeiro "1" -- "0..*" Fila
Servico "1" -- "0..*" Fila
Fila "1" *-- "0..*" Oferta
Oferta "0..1" -- "0..1" Atendimento
Usuario "1" -- "0..*" Recompensa
Usuario "1" -- "0..*" Credito
Atendimento "1" -- "0..1" Credito
Recompensa "0..1" -- "0..*" Credito
Atendimento "0..1" -- "0..1" Recompensa
Servico "1" -- "0..*" Consumo
Insumo "1" -- "0..*" Consumo
Insumo "1" -- "0..*" Movimento
Atendimento "0..1" -- "0..*" Movimento
Atendimento "1" -- "0..1" Receita
Atendimento "1" -- "0..1" Comissao
Atendimento "1" -- "0..1" Avaliacao
Usuario "1" -- "0..*" Despesa : administrador
Usuario "1" -- "0..*" Notificacao
```

## Casos de uso (representação Mermaid)

```mermaid
flowchart LR
 C[Cliente] --> U1([Agendar])
 C --> U2([Cancelar ou reagendar])
 C --> U3([Entrar na fila])
 C --> U4([Avaliar atendimento])
 C --> U5([Consultar histórico])
 C --> U6([Usar recompensa])
 B[Barbeiro] --> U7([Gerenciar atendimento])
 B --> U8([Consultar desempenho])
 A[Administrador] --> U9([Gerenciar catálogo e expediente])
 A --> U10([Gerenciar estoque])
 A --> U11([Consultar financeiro])
 U1 -. "«include»" .-> V([Validar disponibilidade])
 U6 -. "«extend»" .-> U1
 U2 -. "«include»" .-> F([Processar vaga liberada])
 U7 -. "«include» na conclusão" .-> T([Registrar efeitos transacionais])
```

## Sequência — cancelamento e fila

```mermaid
sequenceDiagram
 actor C as Cliente
 participant R as Rota agenda
 participant S as Scheduling
 participant F as Waitlist
 participant D as SQLite
 C->>R: POST cancelar + CSRF
 R->>D: BEGIN IMMEDIATE
 R->>S: cancel(id, cliente)
 S->>D: verificar titularidade e estado
 S->>D: marcar CANCELADO e liberar recompensa
 S->>F: offer_slot(serviço, barbeiro, intervalo)
 F->>D: verificar disponibilidade e ordem FIFO
 alt Cliente compatível
 F->>D: inserir oferta e notificação
 else Fila sem compatível
 F-->>S: horário livre
 end
 R->>D: COMMIT
 R-->>C: redirecionar à agenda
 Note over R,D: Exceção implica rollback
```

Modelo de domínio, estados e sequência de conclusão: [spec.md](../spec.md).
