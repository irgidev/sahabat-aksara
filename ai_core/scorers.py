"""
Scoring Engine V7 — Clean Slate
================================
Philosophy:
- NO free points. You earn every point by matching the target.
- Skeleton is the KING of shape discrimination.
- Structural checks PUNISH when key features are missing.
- HOG/SSIM/distance/completeness are SUPPORTING only.
- All scores on 0-100 scale. Raw and honest.
"""

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim_metric
from skimage.feature import hog as skimage_hog
from scipy.ndimage import distance_transform_edt






class BaseScorer:
    name = "base"
    description = "Base scorer"

    def __init__(self, config=None):
        self.config = config or {}

    def score(self, user_img, template_img, char_target="A", **kwargs):
        return 0.0, {}

    def _kid_friendly_curve(self, raw_score):
        """V7: Minimal boost. Let natural scores speak."""
        raw_score = max(0, min(100, raw_score))
        if raw_score >= 85:
            return min(100, raw_score + 4)
        elif raw_score >= 60:
            return raw_score + 3
        elif raw_score >= 30:
            return raw_score + 1
        else:
            return max(raw_score * 1.1, 2)






class SkeletonMatchScorer(BaseScorer):
    """
    Compares skeletonized images.
    This is the ONLY reliable shape discriminator.
    Tolerance=5px means skeleton pixels must be within 5px of template.
    """
    name = "skeleton"
    description = "Skeleton structure match"

    def __init__(self, config=None):
        super().__init__(config)
        sc = config.get('scorer_config', {}).get('skeleton', {}) if config else {}
        self.tolerance_px = sc.get('tolerance_px', 5)

    def _get_skeleton(self, img):
        """Extract skeleton from binary image."""
        skel = np.zeros_like(img)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        while True:
            eroded = cv2.erode(img, element)
            temp = cv2.dilate(eroded, element)
            temp = cv2.subtract(img, temp)
            skel = cv2.bitwise_or(skel, temp)
            img = eroded.copy()
            if cv2.countNonZero(img) == 0:
                break
        return skel

    def score(self, user_img, template_img, char_target="A", **kwargs):
        user_bin = (user_img > 127).astype(np.uint8) * 255
        tmpl_bin = (template_img > 127).astype(np.uint8) * 255

        user_skel = self._get_skeleton(user_bin.copy())
        tmpl_skel = self._get_skeleton(tmpl_bin.copy())


        if cv2.countNonZero(user_skel) == 0:
            return 1.0, {'reason': 'empty_skeleton'}

        dist = distance_transform_edt(
            (255 - user_skel).astype(np.float32),
            sampling=None
        )


        match_mask = dist <= self.tolerance_px
        matched = np.sum(match_mask & (tmpl_skel > 0))
        total = max(cv2.countNonZero(tmpl_skel), 1)

        raw = (matched / total) * 100
        detail = {
            'tolerance_px': self.tolerance_px,
            'matched': int(matched),
            'total': int(total),
            'raw': round(raw, 1),
        }
        return self._kid_friendly_curve(raw), detail






class EuclideanDistanceScorer(BaseScorer):
    """
    Average pixel distance between user and template strokes.
    Lower distance = better. But CANNOT distinguish shapes!
    Only measures position/size similarity.
    """
    name = "distance"
    description = "Average pixel distance"

    def score(self, user_img, template_img, char_target="A", **kwargs):
        user_pts = np.argwhere(user_img > 127)
        tmpl_pts = np.argwhere(template_img > 127)

        if len(user_pts) < 10 or len(tmpl_pts) < 10:
            return 8.0, {'reason': 'too_few_pixels'}


        from scipy.spatial import cKDTree
        tree = cKDTree(tmpl_pts)
        distances, _ = tree.query(user_pts, k=1)
        avg_dist = float(np.mean(distances))


        raw = max(0, 100 - (avg_dist * 4))

        detail = {
            'avg_distance': round(avg_dist, 2),
            'n_user_pts': len(user_pts),
            'n_template_pts': len(tmpl_pts),
        }
        return self._kid_friendly_curve(raw), detail






class CompletenessScorer(BaseScorer):
    """
    How much of the template does the user's drawing cover?
    Uses dilation to allow for slight position offset.
    NOTE: Cannot distinguish shapes! A line covers some of any letter.
    """
    name = "completeness"
    description = "Template coverage"

    def score(self, user_img, template_img, char_target="A", **kwargs):
        user_bin = (user_img > 127).astype(np.uint8)
        tmpl_bin = (template_img > 127).astype(np.uint8)

        if cv2.countNonZero(tmpl_bin) == 0:
            return 50.0, {'reason': 'empty_template'}


        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 6))
        dilated = cv2.dilate(user_bin, kernel, iterations=1)

        covered = cv2.bitwise_and(dilated, tmpl_bin)
        coverage = cv2.countNonZero(covered) / max(cv2.countNonZero(tmpl_bin), 1)

        raw = coverage * 100

        detail = {
            'coverage_pct': round(raw, 1),
            'user_pixels': cv2.countNonZero(user_bin),
            'template_pixels': cv2.countNonZero(tmpl_bin),
        }
        return self._kid_friendly_curve(raw), detail






class StructuralFeatureScorer(BaseScorer):
    """
    Checks character-specific structural features.
    - Enclosed regions (O, D, B, 0, 6, 8, 9 have holes)
    - Vertical symmetry (A, H, I, M, O, T, U, V, W, X, Y)
    - Horizontal lines (E, F, L, T)
    - Diagonal features (A, K, M, N, R, V, W, X, Y, Z)
    
    V7: NO base score. Must EARN each point with matching features.
    """
    name = "structural"
    description = "Character-specific structural features"


    FEATURES = {

        'A':  ['has_enclosed', 'symmetric_v'],
        'B':  ['has_enclosed', 'vertical_stem'],
        'D':  ['has_enclosed', 'vertical_stem'],
        'O':  ['has_enclosed', 'symmetric_hv', 'round_shape'],
        'P':  ['has_enclosed', 'vertical_stem'],
        'Q':  ['has_enclosed', 'round_shape'],
        'R':  ['has_enclosed', 'diagonal_leg'],
        'a':  ['has_enclosed', 'round_shape'],
        'b':  ['has_enclosed', 'vertical_stem'],
        'd':  ['has_enclosed', 'vertical_stem'],
        'e':  ['has_enclosed', 'round_shape'],
        'g':  ['has_enclosed', 'descender'],
        'o':  ['has_enclosed', 'round_shape'],
        'p':  ['has_enclosed', 'descender'],
        'q':  ['has_enclosed', 'descender'],
        '0':  ['has_enclosed', 'round_shape', 'symmetric_hv'],
        '4':  ['vertical_stem', 'diagonal_leg'],
        '6':  ['has_enclosed', 'round_shape'],
        '8':  ['has_enclosed_2', 'symmetric_v'],
        '9':  ['has_enclosed', 'round_shape'],

        'H':  ['symmetric_hv', 'vertical_stem_x2'],
        'I':  ['symmetric_hv', 'vertical_stem'],
        'M':  ['symmetric_v', 'vertical_stem_x2'],
        'T':  ['symmetric_h', 'horizontal_top'],
        'U':  ['symmetric_v', 'curve_bottom'],
        'V':  ['symmetric_v', 'diagonal_x2'],
        'W':  ['symmetric_v', 'diagonal_x2'],
        'X':  ['symmetric_hv', 'diagonal_x2'],
        'Y':  ['symmetric_v', 'diagonal_x2'],

        'E':  ['horizontal_mid', 'vertical_stem'],
        'F':  ['horizontal_top', 'vertical_stem'],
        'L':  ['vertical_stem', 'horizontal_bottom'],

        'Z':  ['diagonal_z_shape', 'horizontal_top', 'horizontal_bottom'],
        'N':  ['diagonal_leg', 'vertical_stem_x2'],
        'K':  ['diagonal_x2', 'vertical_stem'],

        '1':  ['vertical_stem', 'small_top'],
        '2':  ['curve_top', 'diagonal_z_shape', 'horizontal_bottom'],
        '3':  ['curve_top', 'curve_bottom'],
        '5':  ['horizontal_top', 'vertical_stem', 'curve_bottom'],
        '7':  ['horizontal_top', 'diagonal_leg'],

        'C':  ['curve_open_right'],
        'G':  ['curve_open_right', 'horizontal_mid'],
        'J':  ['curve_bottom', 'hook'],
        'S':  ['s_curve'],
        'c':  ['curve_open_right'],
        'f':  ['horizontal_top', 'curve_top'],
        'h':  ['vertical_stem_x2'],
        'i':  ['vertical_stem', 'dot_above'],
        'j':  ['dot_above', 'curve_bottom'],
        'k':  ['diagonal_x2', 'vertical_stem'],
        'l':  ['vertical_stem'],
        'm':  ['vertical_stem_x3'],
        'n':  ['vertical_stem_x2'],
        'r':  ['vertical_stem', 'curve_top'],
        's':  ['s_curve'],
        't':  ['vertical_stem', 'horizontal_top'],
        'u':  ['curve_bottom'],
        'v':  ['diagonal_x2'],
        'w':  ['diagonal_x2'],
        'x':  ['diagonal_x2'],
        'y':  ['diagonal_x2', 'descender'],
        'z':  ['diagonal_z_shape'],
    }

    def score(self, user_img, template_img, char_target="A", **kwargs):
        char_upper = char_target.upper()
        required = self.FEATURES.get(char_upper, [])
        
        if not required:
            return 35.0, {'reason': 'no_features_defined'}

        user_bin = (user_img > 127).astype(np.uint8)
        results = {}
        
        for feat in required:
            results[feat] = self._check_feature(feat, user_bin, template_img)


        matches = sum(1 for v in results.values() if v)
        total = len(required)
        raw = (matches / max(total, 1)) * 100
        
        detail = {
            'required_features': required,
            'feature_results': {k: bool(v) for k, v in results.items()},
            'matches': f'{matches}/{total}',
        }
        return self._kid_friendly_curve(raw), detail

    def _check_feature(self, feature, user_bin, template_img):
        """Check a single structural feature. Returns True/False."""
        h, w = user_bin.shape
        
        if feature == 'has_enclosed':
            return self._has_enclosed_region(user_bin)
        elif feature == 'has_enclosed_2':
            return self._count_enclosed_regions(user_bin) >= 2
        elif feature.startswith('symmetric'):
            return self._check_symmetry(user_bin, feature)
        elif feature == 'vertical_stem':
            return self._has_vertical_stem(user_bin, count=1)
        elif feature == 'vertical_stem_x2':
            return self._has_vertical_stem(user_bin, count=2)
        elif feature == 'vertical_stem_x3':
            return self._has_vertical_stem(user_bin, count=3)
        elif feature == 'horizontal_top':
            return self._has_horizontal_line(user_bin, region='top')
        elif feature == 'horizontal_mid':
            return self._has_horizontal_line(user_bin, region='mid')
        elif feature == 'horizontal_bottom':
            return self._has_horizontal_line(user_bin, region='bottom')
        elif feature == 'diagonal_leg' or feature == 'diagonal_x2':
            return self._has_diagonal(user_bin, feature)
        elif feature == 'diagonal_z_shape':
            return self._has_z_shape(user_bin)
        elif feature == 'round_shape':
            return self._is_round(user_bin)
        elif feature == 'curve_top':
            return self._has_curve(user_bin, region='top')
        elif feature == 'curve_bottom':
            return self._has_curve(user_bin, region='bottom')
        elif feature == 'curve_open_right':
            return self._is_c_shape(user_bin)
        elif feature == 's_curve':
            return self._is_s_shape(user_bin)
        elif feature == 'descender':
            return self._has_descender(user_bin)
        elif feature == 'dot_above':
            return self._has_dot_above(user_bin)
        elif feature == 'small_top':
            return self._has_small_top(user_bin)
        elif feature == 'hook':
            return self._has_hook(user_bin)
        return False

    def _has_enclosed_region(self, img):
        """Check if image has at least one enclosed (hole) region."""
        inverted = cv2.bitwise_not(img)
        num_labels, _ = cv2.connectedComponents(inverted)
        return num_labels >= 3

    def _count_enclosed_regions(self, img):
        """Count number of enclosed regions."""
        inverted = cv2.bitwise_not(img)
        num_labels, _ = cv2.connectedComponents(inverted)
        return max(0, num_labels - 2)

    def _check_symmetry(self, img, mode):
        """Check vertical/horizontal symmetry."""
        h, w = img.shape
        if mode.endswith('_hv') or mode.endswith('_h'):
            left = img[:, :w//2]
            right_f = img[:, w - w//2:]
            if left.shape[1] != right_f.shape[1]:
                m = min(left.shape[1], right_f.shape[1])
                left = left[:, :m]
                right_f = right_f[:, :m]
            right_flipped = np.fliplr(right_f)
            sim = np.sum(left == right_flipped) / left.size
            if mode.endswith('_hv'): return sim > 0.55
            return sim > 0.45
        if mode.endswith('_v'):
            top = img[:h//2, :]
            bottom_f = img[h - h//2:, :]
            if top.shape[0] != bottom_f.shape[0]:
                m = min(top.shape[0], bottom_f.shape[0])
                top = top[:m, :]
                bottom_f = bottom_f[:m, :]
            bottom_flipped = np.flipud(bottom_f)
            sim = np.sum(top == bottom_flipped) / top.size
            return sim > 0.40

    def _has_vertical_stem(self, img, count=1):
        """Check for vertical line(s)."""
        col_sums = np.sum(img > 0, axis=0)
        threshold = img.shape[0] * 0.30
        stems = np.sum(col_sums >= threshold)
        return stems >= count

    def _has_horizontal_line(self, img, region='top'):
        """Check for horizontal line in specified region."""
        row_sums = np.sum(img > 0, axis=1)
        h = img.shape[0]
        if region == 'top':
            rows = row_sums[:int(h*0.30)]
        elif region == 'bottom':
            rows = row_sums[int(h*0.70):]
        else:
            rows = row_sums[int(h*0.35):int(h*0.65)]
        threshold = img.shape[1] * 0.20
        return np.any(rows >= threshold)

    def _has_diagonal(self, img, mode):
        """Check for diagonal stroke(s)."""
        edges = cv2.Canny(img, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=8,
                                  minLineLength=8, maxLineGap=4)
        if lines is None:
            return False
        diagonals = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx, dy = abs(x2-x1), abs(y2-y1)
            if dx > 4 and dy > 4:
                angle = abs(np.degrees(np.arctan2(dy, dx)))
                if 25 <= angle <= 75 or 105 <= angle <= 165:
                    diagonals += 1
        if mode == 'diagonal_x2':
            return diagonals >= 2
        return diagonals >= 1

    def _has_z_shape(self, img):
        """Check for Z-like shape (top horiz + diagonal + bottom horiz)."""
        has_top = self._has_horizontal_line(img, 'top')
        has_bot = self._has_horizontal_line(img, 'bottom')
        has_diag = self._has_diagonal(img, 'diagonal_leg')
        return has_top and has_bot and has_diag

    def _is_round(self, img):
        """Check if shape is roughly circular/oval."""
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            return False
        circularity = 4 * np.pi * area / (perimeter ** 2)
        return circularity > 0.45

    def _has_curve(self, img, region='top'):
        """Check for curved stroke in region."""
        edges = cv2.Canny(img, 50, 150)
        h, w = img.shape
        if region == 'top':
            roi = edges[:int(h*0.40), :]
        elif region == 'bottom':
            roi = edges[int(h*0.60):, :]
        else:
            return False
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, threshold=6,
                                 minLineLength=6, maxLineGap=4)
        edge_density = np.sum(roi > 0) / max(roi.size, 1)

        is_curved = edge_density > 0.08 and (lines is None or len(lines) < 4)
        return is_curved

    def _is_c_shape(self, img):
        """Check for C-like open curve."""
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            return False
        circ = 4 * np.pi * area / (perimeter ** 2)

        return 0.25 < circ < 0.65 and not self._has_enclosed_region(img)

    def _is_s_shape(self, img):
        """Check for S-curve pattern."""
        h, w = img.shape
        top_half = img[:h//2, :]
        bot_half = img[h//2:, :]

        top_com = cv2.moments(top_half)
        bot_com = cv2.moments(bot_half)
        if top_com['m00'] < 10 or bot_com['m00'] < 10:
            return False
        top_cx = top_com['m10'] / top_com['m00']
        bot_cx = bot_com['m10'] / bot_com['m00']
        mid_x = w / 2

        return (top_cx > mid_x and bot_cx < mid_x) or (top_cx < mid_x and bot_cx > mid_x)

    def _has_descender(self, img):
        """Check for stroke below baseline (bottom 30%)."""
        h = img.shape[0]
        bottom = img[int(h*0.70):, :]
        return np.sum(bottom > 0) > (img.shape[1] * h * 0.05)

    def _has_dot_above(self, img):
        """Check for dot above main body."""
        h, w = img.shape
        top_region = img[:int(h*0.30), :]
        main_body = img[int(h*0.30):, :]
        top_density = np.sum(top_region > 0) / max(top_region.size, 1)
        main_density = np.sum(main_body > 0) / max(main_body.size, 1)

        return top_density > 0.08 and main_density > 0.12

    def _has_small_top(self, img):
        """Check for small feature at top (like number 1's hook)."""
        h, w = img.shape
        top = img[:int(h*0.25), :]
        density = np.sum(top > 0) / max(top.size, 1)
        return density > 0.06

    def _has_hook(self, img):
        """Check for hook/curve at bottom (like J)."""
        h, w = img.shape
        bottom = img[int(h*0.65):, :]
        density = np.sum(bottom > 0) / max(bottom.size, 1)
        return density > 0.08






class StrokeCountScorer(BaseScorer):
    """
    Checks if stroke count is reasonable for the character.
    V7: Very light touch — just checks not wildly off.
    """
    name = "stroke_count"
    description = "Stroke count reasonableness"

    EXPECTED_STROKES = {
        'A': (1, 3), 'B': (1, 3), 'C': (1, 2), 'D': (1, 2), 'E': (1, 4),
        'F': (1, 3), 'G': (1, 3), 'H': (2, 4), 'I': (1, 3), 'J': (1, 2),
        'K': (2, 4), 'L': (1, 2), 'M': (1, 4), 'N': (2, 4), 'O': (1, 2),
        'P': (1, 3), 'Q': (1, 3), 'R': (1, 4), 'S': (1, 2), 'T': (1, 3),
        'U': (1, 3), 'V': (1, 3), 'W': (1, 4), 'X': (1, 3), 'Y': (2, 4),
        'Z': (1, 3), '0': (1, 2), '1': (1, 2), '2': (1, 3), '3': (1, 3),
        '4': (1, 3), '5': (1, 3), '6': (1, 3), '7': (1, 2), '8': (1, 3),
        '9': (1, 3),
    }

    def score(self, user_img, template_img, char_target="A", **kwargs):
        n_strokes = kwargs.get('stroke_count', 1)
        expected = self.EXPECTED_STROKE_COUNT.get(char_target, (1, 4))
        lo, hi = expected

        if lo <= n_strokes <= hi:
            raw = 90.0
        elif n_strokes < lo:
            raw = 50.0 + (n_strokes / max(lo, 1)) * 30
        else:
            raw = 70.0 - ((n_strokes - hi) * 10)

        return self._kid_friendly_curve(max(5, min(95, raw))), {
            'strokes': n_strokes,
            'expected': expected,
        }






class HOGScorer(BaseScorer):
    """
    HOG feature comparison.
    V7: PASS-THROUGH mostly. HOG cannot distinguish similar shapes well.
    """
    name = "hog"
    description = "Gradient histogram comparison"

    def score(self, user_img, template_img, char_target="A", **kwargs):
        try:
            user_gray = user_img.astype(np.uint8)
            tmpl_gray = template_img.astype(np.uint8)

            user_feat = skimage_hog(user_gray, orientations=8,
                                     pixels_per_cell=(8, 8),
                                     cells_per_block=(2, 2),
                                     feature_vector=True,
                                     transform_sqrt=True)
            tmpl_feat = skimage_hog(tmpl_gray, orientations=8,
                                     pixels_per_cell=(8, 8),
                                     cells_per_block=(2, 2),
                                     feature_vector=True,
                                     transform_sqrt=True)

            norm_u = np.linalg.norm(user_feat)
            norm_t = np.linalg.norm(tmpl_feat)
            if norm_u < 1e-6 or norm_t < 1e-6:
                return 10.0, {'reason': 'no_features'}

            cos_sim = np.dot(user_feat, tmpl_feat) / (norm_u * norm_t)
            raw = max(0, min(100, (cos_sim + 1) * 50))

            detail = {'cosine_sim': round(cos_sim, 4), 'raw': round(raw, 1)}
            return self._kid_friendly_curve(raw), detail
        except Exception as e:
            return 15.0, {'error': str(e)[:80]}






class SSIMScorer(BaseScorer):
    """
    SSIM comparison with Gaussian blur pre-processing.
    V7: Light boost only. SSIM is sensitive to position more than shape.
    """
    name = "ssim"
    description = "Structural similarity index"

    def score(self, user_img, template_img, char_target="A", **kwargs):
        try:
            u = cv2.GaussianBlur(user_img.astype(np.uint8), (3, 3), 0.8)
            t = cv2.GaussianBlur(template_img.astype(np.uint8), (3, 3), 0.8)

            ssim_val, _ = ssim_metric(u, t, full=True, data_range=255)
            raw = max(0, min(100, ssim_val * 100))

            detail = {'ssim_raw': round(ssim_val, 4)}
            return self._kid_friendly_curve(raw), detail
        except Exception as e:
            return 15.0, {'error': str(e)[:80]}






SCORER_REGISTRY = {
    'skeleton':       SkeletonMatchScorer,
    'distance':       EuclideanDistanceScorer,
    'completeness':   CompletenessScorer,
    'structural':     StructuralFeatureScorer,
    'stroke_count':   StrokeCountScorer,
    'hog':            HOGScorer,
    'ssim':           SSIMScorer,
}
