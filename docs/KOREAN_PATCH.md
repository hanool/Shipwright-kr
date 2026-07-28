# SoH용 한마루 한국어 패치

이 브랜치는 일본판 Ocarina of Time N64 1.1의 한마루 한국어 패치 v1.102를
적용하는 SoH용 모드를 작성합니다.

## 원본 및 이용 규칙

한국어 패치의 원본 제작자는 **한마루**입니다. 패치를 사용하기 전에 [원본
게시물](https://hanmarus.tistory.com/157)의 이용 규칙을 읽고 준수하세요.

패치 파일은 원작자 허가 없이 재배포하지 말고 원본 게시물 링크를
공유하세요. 패치 및 ROM의 상업적 이용도 금지되어 있습니다. 이 저장소에는
패치와 원본ROM 파일을 포함하지 않습니다.

## 입력 파일

Big Endian `.z64` 형식만 지원합니다.

| 파일 | 크기 | MD5 | SHA-1 |
| - | - | - | - |
| 일본판 1.1 원본 | `33554432` | `1bf5f42b98c3e97948f01155f12e2d88` | `dbfc81f655187dc6fefd93fa6798face770d579d` |
| 한마루 v1.102 적용본 | `33554432` | `d4091f8260a0e1aa5eb8681f1021c314` | `ccbb74e30bd87f3da9b0dac9f05609ad33175f26` |

한국어 적용본의 추가 식별자는 다음과 같습니다.

- N64 CRC1: `1F29ED87`
- CRC32C: `C0AE6EBD`

Xdelta 3.0 이상으로 원본 ROM에 한마루 패치를 적용합니다.

```bash
xdelta3 -d -s "oot-jp11.z64" "patch.xdelta" "oot-korean.z64"
```

해시는 플랫폼 기본 도구나 Python으로 확인할 수 있습니다.

```bash
python3 -c "import hashlib,pathlib; p=pathlib.Path('oot-korean.z64'); d=p.read_bytes(); print(len(d), hashlib.md5(d).hexdigest(), hashlib.sha1(d).hexdigest())"
```

Windows에서는 `python3` 대신 `py -3`을 사용할 수 있습니다.

## 빌드

`korean-patch` 브랜치를 체크아웃하고 서브모듈을 초기화한 뒤 기존 Shipwright
빌드 절차를 따릅니다.

```bash
git switch korean-patch
git submodule update --init --recursive
```

- [Shipwright 빌드 안내](BUILDING.md)

원본 O2R과 한국어 O2R은 반드시 같은 커밋과 같은 빌드에서 추출해야 합니다.

## 전체 O2R 추출

### 1. 원본 일본판

빌드한 SoH의 헤드리스 추출 명령에 원본 ROM과 출력 폴더를 전달합니다.

```bash
"/path/to/soh" --extract-only "/path/to/oot-jp11.z64" "/path/to/jp-output"
```

추출 결과는 `/path/to/jp-output/oot.o2r`입니다.

### 2. 한국어 적용본

같은 실행 파일로 한국어 ROM을 별도 출력 폴더에 추출합니다.

```bash
"/path/to/soh" --extract-only "/path/to/oot-korean.z64" "/path/to/korean-output"
```

추출 결과는 `/path/to/korean-output/oot.o2r`입니다. 이 명령은 창이나 게임
루프를 시작하지 않습니다.

최종적으로 다음 두 파일이 필요합니다.

```text
/path/to/jp-output/oot.o2r
/path/to/korean-output/oot.o2r
```

## 모드 생성

저장소 루트에서 다음 명령을 실행합니다. 출력 경로의 상위 `mods` 폴더는
미리 생성되어 있어야 합니다.

```bash
python3 tools/validate_korean_o2r.py \
  "/path/to/jp-output/oot.o2r" \
  "/path/to/korean-output/oot.o2r"

python3 tools/create_o2r_patch.py \
  "/path/to/jp-output/oot.o2r" \
  "/path/to/korean-output/oot.o2r" \
  "/path/to/SoH/mods/hanmaru-korean.o2r"
```

PowerShell에서는 `python3` 대신 `py -3`을 사용하고 줄 연결 문자를 `` ` ``로
바꾸거나 명령을 한 줄로 입력합니다.

검증기는 한국어 O2R에 예상하지 않은 `code` 또는 오버레이 변경과 리소스
추가·누락이 없는지 확인합니다. 검증 실패 시 차등 모드를 만들기 전에 추출
결과를 조사해야 합니다.

## 검증

```bash
python3 -m zipfile -t "/path/to/SoH/mods/hanmaru-korean.o2r"
python3 -c "import zipfile; print(len(zipfile.ZipFile('/path/to/SoH/mods/hanmaru-korean.o2r').infolist()))"
```

아카이브 검사가 성공하고 항목 수가 `3449`이면 정상입니다. Windows에서는
`python3` 대신 `py -3`을 사용합니다.

생성기 테스트는 다음 명령으로 실행합니다.

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'
```

## 참고
- SoH 설정에서 일본어로 언어를 변경해야 패치가 적용됩니다.
