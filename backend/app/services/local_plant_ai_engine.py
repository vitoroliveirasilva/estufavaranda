from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

Confidence = Literal["low", "medium", "high"]
Intent = Literal["yellow_leaves", "wilt", "watering", "pest", "generic"]


@dataclass(frozen=True)
class LocalPlantAiResult:
    answer: str
    confidence: Confidence
    considered_context: dict[str, Any]


class LocalPlantAiEngine:
    def answer(self, *, question: str, context: dict[str, Any]) -> LocalPlantAiResult:
        normalized_question = self._normalize(question)
        intent = self._classify_intent(normalized_question)
        considered_context = self._build_considered_context(context)
        confidence = self._resolve_confidence(
            intent=intent,
            context=context,
            considered_context=considered_context,
        )

        if intent == "yellow_leaves":
            answer = self._answer_yellow_leaves(
                context=context,
                considered_context=considered_context,
            )
        elif intent == "wilt":
            answer = self._answer_wilt(
                context=context,
                considered_context=considered_context,
            )
        elif intent == "watering":
            answer = self._answer_watering(
                context=context,
                considered_context=considered_context,
            )
        elif intent == "pest":
            answer = self._answer_pest(
                context=context,
                considered_context=considered_context,
            )
        else:
            answer = self._answer_generic(
                context=context,
                considered_context=considered_context,
            )

        return LocalPlantAiResult(
            answer=answer,
            confidence=confidence,
            considered_context=considered_context,
        )

    def _classify_intent(self, normalized_question: str) -> Intent:
        if self._contains_any(
            normalized_question,
            (
                "folha amarela",
                "folhas amarelas",
                "amarela",
                "amarelas",
                "amarelada",
                "amareladas",
                "yellow",
            ),
        ):
            return "yellow_leaves"

        if self._contains_any(
            normalized_question,
            (
                "murcha",
                "murcho",
                "murchando",
                "caida",
                "caidas",
                "caindo",
                "wilt",
            ),
        ):
            return "wilt"

        if self._contains_any(
            normalized_question,
            (
                "regar",
                "rega",
                "agua",
                "molhar",
                "sede",
                "umidade",
                "substrato seco",
                "frequencia",
                "quantas vezes",
                "quando rego",
                "quando devo regar",
            ),
        ):
            return "watering"

        if self._contains_any(
            normalized_question,
            (
                "praga",
                "inseto",
                "cochonilha",
                "pulg",
                "acaro",
                "fungo",
                "mancha",
                "bicho",
            ),
        ):
            return "pest"

        return "generic"

    def _build_considered_context(self, context: dict[str, Any]) -> dict[str, Any]:
        events = self._event_types(context)
        watering = context.get("watering_summary") or {}

        watering_score = self._int_or_none(
            watering.get("score", watering.get("watering_score"))
        )
        last_watering_days = self._int_or_none(
            watering.get("days_since_last_watering", watering.get("last_watering_days"))
        )

        recent_heat = bool(watering.get("recent_heat")) or self._has_recent_heat(
            context
        )

        risk_level = watering.get("risk_level")
        if not risk_level:
            risk_level = self._derive_risk_level(
                events=events,
                watering_score=watering_score,
                recent_heat=recent_heat,
            )

        return {
            "last_watering_days": last_watering_days,
            "recent_heat": recent_heat,
            "recent_repotting": "repotting" in events,
            "recent_wilt": "wilt" in events,
            "recent_yellow_leaves": "yellow_leaves" in events,
            "recent_pest": "pest" in events,
            "risk_level": risk_level,
            "watering_score": watering_score,
        }

    def _resolve_confidence(
        self,
        *,
        intent: Intent,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> Confidence:
        has_clear_question = intent != "generic"
        evidence_count = 0

        if considered_context.get("last_watering_days") is not None:
            evidence_count += 1

        if considered_context.get("watering_score") is not None:
            evidence_count += 1

        if context.get("recent_events"):
            evidence_count += 1

        if context.get("recent_climate"):
            evidence_count += 1

        plant = context.get("plant") or {}
        if any(
            plant.get(key)
            for key in (
                "environment",
                "light_exposure",
                "ventilation",
                "substrate_description",
                "notes",
            )
        ):
            evidence_count += 1

        if has_clear_question and evidence_count >= 4:
            return "high"

        if has_clear_question and evidence_count >= 2:
            return "medium"

        if evidence_count >= 3:
            return "medium"

        return "low"

    def _answer_yellow_leaves(
        self,
        *,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> str:
        plant = context.get("plant") or {}
        causes = []

        if considered_context["recent_yellow_leaves"]:
            causes.append("o próprio histórico já registrou folhas amarelas recentemente")

        if considered_context["recent_repotting"]:
            causes.append("o replantio recente pode ter causado estresse de adaptação")

        if considered_context["recent_heat"]:
            causes.append("calor recente pode ter acelerado perda de água e estressado folhas")

        if considered_context["recent_pest"]:
            causes.append("há registro recente de praga, então vale inspecionar verso das folhas e hastes")

        watering_score = considered_context.get("watering_score")
        if watering_score is not None and watering_score >= 75:
            causes.append("o histórico de rega sugere atenção para possível sede")
        elif watering_score is not None and watering_score <= 35:
            causes.append("não parece haver urgência de rega pelo score atual, então excesso de água também deve ser descartado olhando o substrato")

        if not causes:
            causes.append("variação de rega, luz, adaptação ao ambiente ou envelhecimento natural de folhas antigas")

        substrate_tip = ""
        if plant.get("substrate_description"):
            substrate_tip = f"\nComo o substrato registrado é “{plant['substrate_description']}”, use isso como referência ao conferir se ele está seco, compacto ou encharcado."

        return (
            "Pelo histórico recente, as folhas amareladas parecem pedir observação antes de qualquer ação brusca.\n\n"
            "Possíveis causas:\n"
            f"1. {causes[0]}.\n"
            f"2. {causes[1] if len(causes) > 1 else 'mudança de luz, ventilação ou rotina de rega também pode influenciar'}.\n"
            f"3. {causes[2] if len(causes) > 2 else 'folhas mais antigas podem amarelar naturalmente, principalmente se novas folhas seguem saudáveis'}.\n\n"
            "O que fazer agora:\n"
            "1. Confira o substrato com o dedo antes de regar novamente, evitando regar só pelo impulso.\n"
            "2. Verifique se há cheiro de terra encharcada, raízes sofrendo, manchas ou pontinhos no verso das folhas.\n"
            "3. Evite trocar a planta de lugar muitas vezes nos próximos dias.\n\n"
            "Observe nos próximos dias:\n"
            "1. Se apenas folhas antigas amarelam, pode ser renovação normal.\n"
            "2. Se folhas novas também amarelam ou aparecem manchas, o caso merece mais atenção."
            f"{substrate_tip}"
        )

    def _answer_wilt(
        self,
        *,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> str:
        plant = context.get("plant") or {}
        causes = []

        if considered_context["recent_wilt"]:
            causes.append("há registro recente de murcha no histórico")

        if considered_context["recent_heat"]:
            causes.append("calor recente pode ter aumentado a transpiração da planta")

        if considered_context["recent_repotting"]:
            causes.append("replantio recente pode causar murcha temporária por estresse")

        last_days = considered_context.get("last_watering_days")
        if last_days is not None:
            if last_days == 0:
                causes.append("houve rega hoje, então vale evitar encharcar novamente sem checar o substrato")
            elif last_days >= 4:
                causes.append(f"a última rega registrada foi há {last_days} dias, então pode haver sede dependendo do substrato")

        if not causes:
            causes.append("a murcha pode vir de sede, calor, raiz estressada, substrato encharcado ou mudança recente de ambiente")

        light = plant.get("light_exposure")
        light_tip = (
            f"\nA luz registrada é “{light}”; confira se ela não recebeu sol mais forte do que o normal."
            if light
            else ""
        )

        return (
            "Pelo histórico recente, a murcha pode ser sinal de estresse hídrico ou ambiental, mas não dá para cravar uma causa única.\n\n"
            "Possíveis causas:\n"
            f"1. {causes[0]}.\n"
            f"2. {causes[1] if len(causes) > 1 else 'substrato seco demais ou úmido demais podem causar aparência parecida'}.\n"
            f"3. {causes[2] if len(causes) > 2 else 'mudança de vaso, local ou temperatura também pode pesar'}.\n\n"
            "O que fazer agora:\n"
            "1. Toque o substrato alguns centímetros abaixo da superfície antes de regar.\n"
            "2. Se estiver seco, regue com calma até hidratar bem; se estiver úmido, espere e melhore ventilação.\n"
            "3. Tire a planta de sol forte direto enquanto ela se recupera.\n\n"
            "Observe nos próximos dias:\n"
            "1. Se ela levanta após hidratação, era provável sede ou calor.\n"
            "2. Se piora mesmo com substrato úmido, investigue raiz, drenagem e pragas."
            f"{light_tip}"
        )

    def _answer_watering(
        self,
        *,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> str:
        plant = context.get("plant") or {}
        last_days = considered_context.get("last_watering_days")
        watering_score = considered_context.get("watering_score")

        if last_days is None:
            last_watering_text = "não encontrei uma última rega registrada com segurança"
        elif last_days == 0:
            last_watering_text = "a última rega registrada foi hoje"
        elif last_days == 1:
            last_watering_text = "a última rega registrada foi ontem"
        else:
            last_watering_text = f"a última rega registrada foi há {last_days} dias"

        if watering_score is None:
            score_text = "não há score suficiente para decidir só pelo histórico"
        elif watering_score >= 80:
            score_text = "o score de rega está alto, então existe sinal de atenção para possível sede"
        elif watering_score >= 60:
            score_text = "o score de rega está moderado, então vale conferir o substrato antes de decidir"
        else:
            score_text = "o score de rega não indica urgência forte agora"

        environment = plant.get("environment")
        environment_tip = (
            f"\nComo o ambiente registrado é “{environment}”, compare isso com calor, vento e velocidade de secagem do substrato."
            if environment
            else ""
        )

        return (
            f"Pelo histórico recente, {last_watering_text} e {score_text}.\n\n"
            "Possíveis pontos de decisão:\n"
            "1. Substrato seco alguns centímetros abaixo da superfície tende a indicar que a rega pode ser necessária.\n"
            "2. Substrato ainda úmido, pesado ou com cheiro ruim pede espera, não mais água.\n"
            "3. Calor, vento e vaso pequeno podem fazer a planta secar mais rápido.\n\n"
            "O que fazer agora:\n"
            "1. Não use uma frequência fixa como regra absoluta.\n"
            "2. Confira a umidade real do substrato antes de regar.\n"
            "3. Se regar, faça uma rega completa e depois deixe drenar bem.\n\n"
            "Observe nos próximos dias:\n"
            "1. Se as folhas firmam após rega, ajuste o acompanhamento da umidade.\n"
            "2. Se amarelam ou murcham com substrato úmido, investigue drenagem e raiz."
            f"{environment_tip}"
        )

    def _answer_pest(
        self,
        *,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> str:
        if considered_context["recent_pest"]:
            intro = "Pelo histórico recente, já existe registro de praga, então vale tratar a suspeita com atenção."
        else:
            intro = "Pelo histórico recente, não encontrei registro claro de praga, mas a inspeção visual ainda é importante."

        return (
            f"{intro}\n\n"
            "Possíveis sinais para conferir:\n"
            "1. Pontinhos brancos, marrons ou pretos no verso das folhas.\n"
            "2. Folhas pegajosas, teias finas, manchas novas ou deformações.\n"
            "3. Insetos próximos às nervuras, brotos e encontro entre folha e caule.\n\n"
            "O que fazer agora:\n"
            "1. Isole a planta se houver suspeita forte, para proteger as outras.\n"
            "2. Limpe folhas afetadas com cuidado e remova partes muito comprometidas.\n"
            "3. Evite aplicar qualquer produto agressivo sem identificar melhor o problema.\n\n"
            "Observe nos próximos dias:\n"
            "1. Se os pontos voltam depois da limpeza.\n"
            "2. Se novas folhas nascem deformadas ou com manchas."
        )

    def _answer_generic(
        self,
        *,
        context: dict[str, Any],
        considered_context: dict[str, Any],
    ) -> str:
        plant = context.get("plant") or {}
        plant_name = plant.get("nickname") or plant.get("name") or "sua planta"

        observed = []

        if considered_context["recent_repotting"]:
            observed.append("houve replantio recente")

        if considered_context["recent_wilt"]:
            observed.append("há registro recente de murcha")

        if considered_context["recent_yellow_leaves"]:
            observed.append("há registro recente de folhas amarelas")

        if considered_context["recent_pest"]:
            observed.append("há registro recente de praga")

        if considered_context["recent_heat"]:
            observed.append("houve sinal de calor recente")

        if not observed:
            observed.append("não há um sinal crítico claro no histórico recente")

        return (
            f"Pelo histórico recente da {plant_name}, {observed[0]}.\n\n"
            "Possíveis pontos para analisar:\n"
            "1. Rotina de rega e umidade real do substrato.\n"
            "2. Mudanças recentes de vaso, local, luz ou ventilação.\n"
            "3. Sinais visuais como manchas, folhas murchas, amarelamento ou pragas.\n\n"
            "O que fazer agora:\n"
            "1. Observe a planta por alguns dias antes de fazer várias mudanças ao mesmo tempo.\n"
            "2. Registre eventos importantes com foto, porque isso melhora bastante a leitura do histórico.\n"
            "3. Se aparecer piora rápida, detalhe o sintoma principal na próxima pergunta.\n\n"
            "Não vou fechar diagnóstico definitivo com poucos sinais, mas consigo te orientar melhor conforme o histórico cresce."
        )

    def _event_types(self, context: dict[str, Any]) -> set[str]:
        return {
            str(event.get("event_type"))
            for event in context.get("recent_events", [])
            if event.get("event_type")
        }

    def _has_recent_heat(self, context: dict[str, Any]) -> bool:
        for snapshot in context.get("recent_climate", []):
            temperature = self._float_or_none(snapshot.get("temperature_c"))
            feels_like = self._float_or_none(snapshot.get("feels_like_c"))

            if temperature is not None and temperature >= 30:
                return True

            if feels_like is not None and feels_like >= 32:
                return True

        return False

    def _derive_risk_level(
        self,
        *,
        events: set[str],
        watering_score: int | None,
        recent_heat: bool,
    ) -> str:
        if "pest" in events or ("wilt" in events and recent_heat):
            return "attention"

        if watering_score is not None and watering_score >= 85:
            return "attention"

        if "yellow_leaves" in events or "wilt" in events or "repotting" in events:
            return "attention"

        return "stable"

    @staticmethod
    def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
        return any(term in value for term in terms)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        return " ".join(without_accents.lower().split())

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
