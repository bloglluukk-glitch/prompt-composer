# Prompt Composer

**한국어** | [English](README.en.md)

**감각적인 요청을, 실행하고 검수할 수 있는 제작 지시로.**

C4D의 움직임·타이밍 관점과 Redshift의 재질·빛·초점·공간 관점을 조합하는 오프라인 도구입니다. 한국어·영어 요청 예제와 두 언어의 프롬프트를 제공합니다. 무엇을 선택했는지, 무엇을 제외했는지, 어떤 근거가 있고 아직 무엇을 검증하지 않았는지도 함께 기록합니다.

**v0.1.0 / experimental.** 실제 이미지·영상·C4D 장면을 생성하지 않습니다. 특정 생성 서비스나 C4D/Redshift 플러그인에 연결하지 않습니다. 프롬프트 조립과 검수 계획을 만들어 사용자가 선택한 도구에서 시험할 수 있게 합니다.

## 바로 실행

Python 3.11 이상이 필요합니다. Python 표준 라이브러리만 사용하므로 별도 패키지 설치는 없습니다. 저장소를 다운로드하고 폴더 안에서 실행합니다.

```sh
python prompt_composer.py --input examples/ko/01_coat_reveal.json --format markdown --language ko
```

영문 결과:

```sh
python prompt_composer.py --input examples/en/01_coat_reveal.json --format markdown --language en
```

짧은 요청으로 시작할 수도 있습니다.

```sh
python prompt_composer.py --brief "새틴 메탈 제품에 좁은 하이라이트가 지나가고 얇은 코팅층이 드러난다." --subject "새틴 메탈 제품" --format markdown --language ko
```

[실제 조립 예제 — 한국어](examples/results/coat_reveal.ko.md) · [English](examples/results/coat_reveal.en.md)

## 요청 → 제작 지시

예: ‘새틴 메탈 제품의 표면이 빛으로 드러나고 마지막에 얇은 코팅 반사가 보였으면 좋겠다.’

도구는 방향성 하이라이트, 절제된 거칠기, 상부 코팅 반사 등을 선택합니다. 전체 물체를 투명하게 만드는 Transmission과 코팅층을 구분하며, 명시한 보존 조건과 출력 조건을 상세 프롬프트에 남깁니다. 선택 점수는 규칙 기반 순위이고 생성 성공률이 아닙니다.

결과 JSON에는 간결·상세 프롬프트의 한국어·영어판, 선택·제외 후보와 점수 근거, 시간 계획, Negative 묶음, 참조 전략, 출처와 미검증 항목이 들어갑니다. Markdown으로 읽기 쉬운 제작 계획을 만들 수도 있습니다.

## 공개한 지식과 예제

지식 카드 **23개**: Motion 4개, Redshift 19개. 코팅 리빌, 내부 산란 역광, 미세 표면 결, 랙 포커스, 안개·빛줄기, 상대 타이밍의 예제를 각각 한국어·영어로 제공합니다. 두 언어의 **12개 예제는 지시 조립 시험**이며 생성 영상의 성공 사례가 아닙니다.

원래의 전체 지식 저장소는 포함하지 않습니다. 이 판은 여섯 가지 사용 흐름에 필요한 공개용 카드와 설정을 제공합니다. 도구 실행에는 C4D·Redshift 설치나 개인 DB가 필요하지 않습니다.

## 검증과 한계

- 동작 검사 20개, 예제 조립 12/12, 한·영 6쌍의 선택 일치, 별도 폴더에서 실행을 확인했습니다. [검증 기록](docs/VALIDATION.json)
- 실제 생성·렌더 시험은 0회입니다. 품질·정확한 타이밍·참조 보존은 같은 모델과 입력으로 따로 비교해야 합니다.
- 영어 프롬프트는 등록된 지식 조각을 조합합니다. 임의 한국어 요청 전체를 번역하는 도구가 아니며, 등록되지 않은 한국어 피사체는 중립적인 영문 표현과 불확실성 표시를 사용합니다.
- 예제의 이미지 파일명은 역할을 설명하는 자리표시자입니다. 이미지 파일은 제공하지 않으며 실행 중 읽거나 업로드하지 않습니다.
- 요청의 출력 조건은 전달하는 지시이지 생성 도구가 지원한다는 보장이 아닙니다. 5단계의 시간 비율도 편집상 제안입니다.

[사용 안내](docs/USAGE.md) · [구조와 선택 규칙](docs/ARCHITECTURE.md) · [출처](SOURCES.md) · [기여](CONTRIBUTING.md) · [공개 보고](docs/RELEASE_REPORT.md)

## 재사용

검수된 공개 코드·설정·카드·문서·예제에는 [MIT License](LICENSE)를 적용합니다. 외부 Maxon 문서·상표·소프트웨어에는 적용되지 않습니다. 이 프로젝트는 Maxon과 제휴하거나 공식 승인을 받은 제품이 아닙니다. 제작자: [bloglluukk-glitch](https://github.com/bloglluukk-glitch). 공개판 구성과 번역에는 Codex의 도움을 받았습니다.

[변경 기록](CHANGELOG.md) · [공개 파일 목록](UPLOAD_MANIFEST.json)
