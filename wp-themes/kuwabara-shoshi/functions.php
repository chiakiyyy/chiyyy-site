<?php
/**
 * 桑原司法書士事務所 — Lightning 子テーマ
 *
 * @package kuwabara-shoshi
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}


/* ==========================================================================
   スタイルシート読み込み
   ========================================================================== */

function kuwabara_shoshi_enqueue_styles() {

	$style_path = get_stylesheet_directory() . '/style.css';

	wp_enqueue_style(
		'kuwabara-shoshi-style',
		get_stylesheet_directory_uri() . '/style.css',
		array(),
		file_exists( $style_path ) ? filemtime( $style_path ) : '1.0.0'
	);
}
add_action( 'wp_enqueue_scripts', 'kuwabara_shoshi_enqueue_styles', 20 );


/* ==========================================================================
   フッター コピーライト
   --------------------------------------------------------------------------
   本番（BizVektor 子テーマ footer.php）の表記を再現する。
     Copyright © 桑原司法書士事務所 All Rights Reserved.
   ========================================================================== */

function kuwabara_shoshi_footer_copyright( $copyright ) {

	$site_url  = esc_url( home_url( '/' ) );
	$site_name = '桑原司法書士事務所';

	$copyright  = '<p class="copyright">';
	$copyright .= 'Copyright &copy; ';
	$copyright .= '<a href="' . $site_url . '">' . esc_html( $site_name ) . '</a>';
	$copyright .= ' All Rights Reserved.';
	$copyright .= '</p>';

	return $copyright;
}
add_filter( 'lightning_footerCopyRightCustom', 'kuwabara_shoshi_footer_copyright' );

function kuwabara_shoshi_footer_powered( $powered ) {
	return '<!-- -->';
}
add_filter( 'lightning_footerPoweredCustom', 'kuwabara_shoshi_footer_powered' );

/* フィルタが効かない場合の CSS フォールバック（style.css Section 4 でも対応） */


/* ==========================================================================
   ヘッダー 連絡先表示
   --------------------------------------------------------------------------
   旧サイト（BizVektor）でヘッダー右上に表示されていた連絡先を再現する。

   使用フック: lightning_site_header_logo_after
   表示値は ExUnit → Main setting → Contact Information から取得する。
   ========================================================================== */

function kw_header_contact() {

	$options = get_option( 'vkExUnit_contact' );

	$message = isset( $options['contact_txt'] ) ? $options['contact_txt'] : '';
	$tel     = isset( $options['tel_number'] ) ? $options['tel_number'] : '';
	$time    = isset( $options['contact_time'] ) ? $options['contact_time'] : '';

	if ( ! $message && ! $tel && ! $time ) {
		return;
	}
	?>
	<div class="kw-header-contact">
		<?php if ( $message ) : ?>
			<p class="kw-header-contact__message"><?php echo esc_html( $message ); ?></p>
		<?php endif; ?>

		<?php if ( $tel ) : ?>
			<p class="kw-header-contact__tel">
				<a href="tel:<?php echo esc_attr( preg_replace( '/[^0-9+]/', '', $tel ) ); ?>">
					TEL <?php echo esc_html( $tel ); ?>
				</a>
			</p>
		<?php endif; ?>

		<?php if ( $time ) : ?>
			<p class="kw-header-contact__time"><?php echo esc_html( $time ); ?></p>
		<?php endif; ?>
	</div>
	<?php
}
add_action( 'lightning_site_header_logo_after', 'kw_header_contact' );


/* ==========================================================================
   ウィジェット見出しタグを h2 に統一
   --------------------------------------------------------------------------
   Lightning のサイドバーウィジェット見出しは、デフォルトで <h2> が出力される
   ことが多いが、プラグインや設定によって <h3>/<h4> になる場合がある。
   style.css の .sub-section .sub-section-title セレクタは h2 を基準としているため、
   ここで h2 に統一する。

   ※ Lightning 本体の設定（カスタマイザー → ウィジェット見出しタグ）で
     h2 が選択されている場合は、この関数は実質無効（二重登録になるが無害）。
   ========================================================================== */

function kuwabara_shoshi_widget_title_tag( $params ) {
	if ( isset( $params[0]['before_title'] ) ) {
		$params[0]['before_title'] = '<h2 class="widget-title sub-section-title">';
		$params[0]['after_title']  = '</h2>';
	}
	return $params;
}
add_filter( 'dynamic_sidebar_params', 'kuwabara_shoshi_widget_title_tag' );


/* ==========================================================================
   フッター 事務所情報
   --------------------------------------------------------------------------
   フッターナビゲーションの下（コピーライトバーの上）に事務所名を表示する。
   使用フック: lightning_footer_inner_end
     → Lightning G3 のフッターテンプレート内、ナビ・ウィジェット領域の直後に
       挿入される。Lightning のバージョンによって異なる場合は F12 → Source で
       footer.php の do_action 名を確認し、必要に応じてフック名を変更すること。
   ========================================================================== */

function kw_footer_office_info() {

	$site_name = get_bloginfo( 'name' );

	/* VK ExUnit の連絡先設定から住所・TEL・FAX を取得 */
	$contact = get_option( 'vkExUnit_contact', array() );
	$address = isset( $contact['address'] )    ? $contact['address']    : '';
	$tel     = isset( $contact['tel_number'] ) ? $contact['tel_number'] : '';
	$fax     = isset( $contact['fax_number'] ) ? $contact['fax_number'] : '';

	/* address が ExUnit contact にない場合は general オプションを確認 */
	if ( ! $address ) {
		$general = get_option( 'vkExUnit_general', array() );
		$address = isset( $general['address'] ) ? $general['address'] : '';
	}

	if ( ! $site_name && ! $address && ! $tel && ! $fax ) {
		return;
	}

	/* HTML を組み立て */
	$html  = '<div class="kw-footer-info"><div class="container">';
	if ( $site_name ) {
		$html .= '<p class="kw-footer-office-name">' . esc_html( $site_name ) . '</p>';
	}
	if ( $address ) {
		$html .= '<p class="kw-footer-office-address">' . esc_html( $address ) . '</p>';
	}
	if ( $tel || $fax ) {
		$parts = array();
		if ( $tel ) { $parts[] = 'TEL: ' . esc_html( $tel ); }
		if ( $fax ) { $parts[] = 'FAX: ' . esc_html( $fax ); }
		$html .= '<p class="kw-footer-office-contact">' . implode( ' / ', $parts ) . '</p>';
	}
	$html .= '</div></div>';

	/* wp_footer フックから JS で .site-footer-copyright の直前に挿入 */
	?>
	<script>
	(function () {
		var html = <?php echo wp_json_encode( $html ); ?>;
		function insert() {
			var el = document.createElement( 'div' );
			el.innerHTML = html;
			var node = el.firstElementChild || el.firstChild;

			/* .site-footer-copyright の直前に挿入（コピーライト帯の上） */
			var copyright = document.querySelector( '.site-footer-copyright' );
			if ( copyright && copyright.parentNode ) {
				copyright.parentNode.insertBefore( node, copyright );
				return;
			}

			/* フォールバック: .site-footer の末尾 */
			var footer = document.querySelector( '.site-footer' );
			if ( footer ) {
				footer.appendChild( node );
			}
		}
		if ( document.readyState === 'loading' ) {
			document.addEventListener( 'DOMContentLoaded', insert );
		} else {
			insert();
		}
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'kw_footer_office_info' );


/* ==========================================================================
   お知らせ一覧 ショートコード [kw_info_list]
   --------------------------------------------------------------------------
   BizVektor がテーマ側で自動出力していた TOPページのお知らせ一覧を再現する。

   使い方:
     [kw_info_list]
     [kw_info_list count="3"]
     [kw_info_list heading=""]   ← 見出し非表示

   カスタム投稿タイプ「info（お知らせ）」を対象とする。
   ========================================================================== */

function kw_info_list_shortcode( $atts ) {

	$atts = shortcode_atts(
		array(
			'count'   => 5,
			'heading' => 'お知らせ',
			'rss'     => 'yes',
			'archive' => 'yes',
		),
		$atts,
		'kw_info_list'
	);

	$query = new WP_Query(
		array(
			'post_type'           => 'info',
			'posts_per_page'      => (int) $atts['count'],
			'post_status'         => 'publish',
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);

	if ( ! $query->have_posts() ) {
		return '';
	}

	ob_start();
	?>
	<div class="kw-info">

		<?php if ( '' !== $atts['heading'] || 'yes' === $atts['rss'] ) : ?>
		<div class="kw-info__head">
			<?php if ( '' !== $atts['heading'] ) : ?>
				<h2 class="kw-info__heading"><?php echo esc_html( $atts['heading'] ); ?></h2>
			<?php endif; ?>

			<?php if ( 'yes' === $atts['rss'] ) : ?>
				<a class="kw-info__rss"
				   href="<?php echo esc_url( get_post_type_archive_feed_link( 'info' ) ); ?>">RSS</a>
			<?php endif; ?>
		</div>
		<?php endif; ?>

		<ul class="kw-info__list">
			<?php
			while ( $query->have_posts() ) :
				$query->the_post();
				?>
				<li class="kw-info__item">
					<h3 class="kw-info__item-title">
						<a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
					</h3>

					<p class="kw-info__date">
						<time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
							<?php echo esc_html( get_the_date() ); ?>
						</time>
					</p>

					<?php $excerpt = get_the_excerpt(); ?>
					<?php if ( $excerpt ) : ?>
						<p class="kw-info__excerpt"><?php echo esc_html( $excerpt ); ?></p>
					<?php endif; ?>

					<p class="kw-info__more">
						<a href="<?php the_permalink(); ?>">この記事を読む</a>
					</p>
				</li>
				<?php
			endwhile;
			wp_reset_postdata();
			?>
		</ul>

		<?php if ( 'yes' === $atts['archive'] ) : ?>
			<p class="kw-info__archive">
				<a href="<?php echo esc_url( get_post_type_archive_link( 'info' ) ); ?>">お知らせ一覧</a>
			</p>
		<?php endif; ?>

	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'kw_info_list', 'kw_info_list_shortcode' );


/* ==========================================================================
   スライダー自動再生を停止
   --------------------------------------------------------------------------
   Lightning の Customizer 設定「スライド静止時間: 0」では自動再生が
   止まらない（0 を falsy として無視する）場合があるため、JS で明示的に
   Swiper の autoplay.stop() を呼び出す。
   ========================================================================== */

function kw_disable_slider_autoplay() {

	if ( ! is_front_page() ) {
		return;
	}
	?>
	<script>
	(function () {
		function stopAutoplay() {
			var el = document.querySelector( '.ltg-slide' );
			if ( ! el ) { return; }

			/* Swiper インスタンスが既にあれば即停止 */
			if ( el.swiper ) {
				el.swiper.autoplay.stop();
				return;
			}

			/* まだ初期化されていない場合は MutationObserver で待つ */
			var observer = new MutationObserver( function () {
				if ( el.swiper ) {
					el.swiper.autoplay.stop();
					observer.disconnect();
				}
			} );
			observer.observe( el, { attributes: true, subtree: true, childList: true } );

			/* 10 秒後に諦める */
			setTimeout( function () { observer.disconnect(); }, 10000 );
		}

		if ( document.readyState === 'loading' ) {
			document.addEventListener( 'DOMContentLoaded', stopAutoplay );
		} else {
			stopAutoplay();
		}
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'kw_disable_slider_autoplay' );


/* ==========================================================================
   ページトップへ戻るボタン 画像置換
   --------------------------------------------------------------------------
   CSS の url() は相対パスで記述しているが、WordPress の設定によっては
   解決されない場合があるため、wp_head で絶対 URL のインライン CSS を追加。
   Lightning / VK ExUnit のボタン要素を確実に対象にするため広いセレクタを使用。
   ========================================================================== */

function kw_pagetop_image_css() {
	$img_url = esc_url( get_stylesheet_directory_uri() . '/images/footer_pagetop.png' );
	echo '<style id="kw-pagetop-css">
/* ページトップ画像 — VK ExUnit / Lightning 全セレクタ対応 */
#vk_back_to_top,
.vk_back_to_top,
#page-top,
.page-top,
[id*="pagetop"],
[class*="pagetop"],
[class*="scroll-top"],
[class*="scrolltop"],
[class*="back-to-top"],
[class*="back_to_top"] {
	width: 45px !important;
	height: 45px !important;
	background-image: url("' . $img_url . '") !important;
	background-size: 45px 45px !important;
	background-repeat: no-repeat !important;
	background-position: center !important;
	background-color: transparent !important;
	border: none !important;
	border-radius: 0 !important;
	box-shadow: none !important;
	opacity: 1 !important;
	font-size: 0 !important;
	color: transparent !important;
	overflow: hidden !important;
	display: block !important;
}
#vk_back_to_top *,
.vk_back_to_top *,
#page-top *,
.page-top *,
[id*="pagetop"] *,
[class*="pagetop"] *,
[class*="back-to-top"] *,
[class*="back_to_top"] * {
	display: none !important;
}
#vk_back_to_top:hover,
.vk_back_to_top:hover,
[id*="pagetop"]:hover,
[class*="pagetop"]:hover,
[class*="back-to-top"]:hover,
[class*="back_to_top"]:hover {
	opacity: 0.75 !important;
}
</style>' . "\n";
}
add_action( 'wp_head', 'kw_pagetop_image_css' );


/* ==========================================================================
   ページトップへ戻るボタン JS 強制置換
   --------------------------------------------------------------------------
   CSS セレクタが一致しない場合のフォールバック。
   DOM から固定配置のスクロールボタンを探し、JS で直接スタイルを当てる。
   ========================================================================== */

function kw_pagetop_image_js() {
	$img_url = esc_url( get_stylesheet_directory_uri() . '/images/footer_pagetop.png' );
	?>
	<script>
	(function () {
		var imgUrl = <?php echo wp_json_encode( $img_url ); ?>;

		var SELECTORS = [
			'#vk_back_to_top', '.vk_back_to_top',
			'#page-top', '.page-top',
			'[id*="pagetop"]', '[class*="pagetop"]',
			'[class*="back-to-top"]', '[class*="back_to_top"]',
			'[class*="scroll-top"]', '[class*="scrolltop"]',
			'[aria-label*="先頭"]', '[aria-label*="top"]'
		];

		function applyImage( el ) {
			/* 既に処理済みなら何もしない */
			if ( el.querySelector( 'img.kw-pagetop-img' ) ) { return; }

			/* 既存の子要素（SVG・icon）を非表示 */
			var children = el.querySelectorAll( '*' );
			for ( var i = 0; i < children.length; i++ ) {
				children[ i ].style.setProperty( 'display', 'none', 'important' );
			}

			/* footer_pagetop.png を img として直接挿入 */
			var img = document.createElement( 'img' );
			img.src    = imgUrl;
			img.alt    = '';
			img.width  = 45;
			img.height = 45;
			img.className = 'kw-pagetop-img';
			img.style.cssText = 'display:block!important;width:45px!important;height:45px!important;max-width:none!important;margin:0!important;padding:0!important;border:none!important;';
			el.appendChild( img );

			/* コンテナを透明化・サイズ整合 */
			el.style.setProperty( 'background',   'transparent', 'important' );
			el.style.setProperty( 'border',        'none',        'important' );
			el.style.setProperty( 'border-radius', '0',           'important' );
			el.style.setProperty( 'box-shadow',    'none',        'important' );
			el.style.setProperty( 'padding',        '0',          'important' );
			el.style.setProperty( 'width',          '45px',       'important' );
			el.style.setProperty( 'height',         '45px',       'important' );
			el.style.setProperty( 'overflow',       'visible',    'important' );
			el.style.setProperty( 'line-height',    '0',          'important' );
		}

		function fixAll() {
			for ( var s = 0; s < SELECTORS.length; s++ ) {
				try {
					var nodes = document.querySelectorAll( SELECTORS[ s ] );
					for ( var n = 0; n < nodes.length; n++ ) {
						applyImage( nodes[ n ] );
					}
				} catch ( e ) {}
			}
		}

		/* 即時実行 */
		fixAll();
		if ( document.readyState === 'loading' ) {
			document.addEventListener( 'DOMContentLoaded', fixAll );
		}

		/* スクロール時（VK ExUnit はスクロール後にボタンを表示） */
		window.addEventListener( 'scroll', function onScroll() {
			fixAll();
			window.removeEventListener( 'scroll', onScroll );
		}, { passive: true } );

		/* MutationObserver: 動的追加 + style/class 変化を監視（30秒） */
		var observer = new MutationObserver( fixAll );
		function startObs() {
			observer.observe( document.body, {
				childList: true,
				subtree: true,
				attributes: true,
				attributeFilter: [ 'style', 'class' ]
			} );
			setTimeout( function () { observer.disconnect(); }, 30000 );
		}
		if ( document.readyState === 'loading' ) {
			document.addEventListener( 'DOMContentLoaded', startObs );
		} else {
			startObs();
		}
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'kw_pagetop_image_js' );
